"""Provides a class for generating acquired data within mock devices."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from abc import ABC, abstractmethod
from threading import Event, Lock
from time import monotonic, sleep
from typing import Dict

from numpy import ndarray
from numpy.random import uniform

from spectrum_gmbh.regs import SPC_DATA_AVAIL_USER_LEN, SPC_DATA_AVAIL_USER_POS
from spectrumdevice.settings import AcquisitionMode
from spectrumdevice.settings.transfer_buffer import NOTIFY_SIZE_PAGE_SIZE_IN_BYTES


TRANSFER_CHUNK_COUNTER = -1  # this is a custom key used in the _para_dict to count the number of transfers


class MockWaveformSource(ABC):
    """Interface for a mock noise waveform source. Implementations are intended to be called in their own thread.
    When called, `MockWaveformSource` implementations will fill a provided buffer with noise samples."""

    def __init__(self, param_dict: Dict[int, int]):
        self._param_dict = param_dict

    @abstractmethod
    def __call__(
        self,
        stop_flag: Event,
        frame_rate: float,
        amplitude: float,
        transfer_buffer_data_array: ndarray,
        samples_per_frame: int,
        buffer_lock: Lock,
    ) -> None:
        raise NotImplementedError()


class SingleModeMockWaveformSource(MockWaveformSource):
    def __call__(
        self,
        stop_flag: Event,
        frame_rate: float,
        amplitude: float,
        transfer_buffer_data_array: ndarray,
        samples_per_frame: int,
        buffer_lock: Lock,
    ) -> None:
        """When called, this MockWaveformSource simulates SPC_REC_STD_SINGLE Mode, placing a single frames worth of
        samples into a provided mock on_device_buffer.

        Args:
            stop_flag (Event): A threading event that will be used in the calling thread to stop the acquisition.
            frame_rate (float): The samples will be generated 1 / frame_rate seconds after __call__ is called.
            amplitude (float): Waveforms will contain random values in the range -amplitude to +amplitude
            on_device_buffer (ndarray): The numpy array into which the noise samples will be written.
            buffer_lock (Lock): A threading lock created in the calling thread that will be used to ensure access to
                the on_device_buffer array is thread safe.

        """
        start_time = monotonic()
        bytes_per_sample = transfer_buffer_data_array.itemsize
        while not stop_flag.is_set() and ((monotonic() - start_time) < (1 / frame_rate)):
            sleep(0.001)
        if not stop_flag.is_set():
            with buffer_lock:
                transfer_buffer_data_array[:samples_per_frame] = uniform(
                    low=-1 * amplitude, high=amplitude, size=samples_per_frame
                )
                self._param_dict[SPC_DATA_AVAIL_USER_POS] = 0
                self._param_dict[SPC_DATA_AVAIL_USER_LEN] = samples_per_frame * bytes_per_sample
            self._param_dict[TRANSFER_CHUNK_COUNTER] += 1


class MultiFIFOModeMockWaveformSource(MockWaveformSource):
    def __init__(self, param_dict: Dict[int, int], notify_size_in_pages: int):
        super().__init__(param_dict)
        self._notify_size_in_pages = notify_size_in_pages

    def __call__(
        self,
        stop_flag: Event,
        frame_rate: float,
        amplitude: float,
        transfer_buffer_data_array: ndarray,
        samples_per_frame: int,
        buffer_lock: Lock,
    ) -> None:
        """When called, this `MockWaveformSource` simulates SPC_REC_FIFO_MULTI Mode, continuously replacing the contents
        of on_device_buffer with new frames of noise samples.

        Args:
            stop_flag (Event): A threading event that will be used in the calling thread to stop the acquisition.
            frame_rate (float): The contents of the on_device_buffer will be updated at this rate (Hz).
            amplitude (float): Waveforms will contain random values from a uniform distribution in the range -amplitude
            to +amplitude
            on_device_buffer (ndarray): The numpy array into which the noise samples will be written.
            buffer_lock (Lock): A threading lock created in the calling thread that will be used to ensure access to
                the on_device_buffer array is thread safe.

        """
        bytes_per_sample = transfer_buffer_data_array.itemsize
        notify_size_in_samples = self._notify_size_in_pages * NOTIFY_SIZE_PAGE_SIZE_IN_BYTES // bytes_per_sample
        notify_size_in_samples = min((samples_per_frame, notify_size_in_samples))
        samples_per_second = frame_rate * samples_per_frame
        notify_sizes_per_second = samples_per_second / notify_size_in_samples
        sample_count = 0
        while not stop_flag.is_set():

            start_sample = sample_count % samples_per_frame
            stop_sample = (sample_count + notify_size_in_samples) % samples_per_frame
            stop_sample = stop_sample if stop_sample else samples_per_frame
            with buffer_lock:
                transfer_buffer_data_array[start_sample:stop_sample] = uniform(
                    low=-1 * amplitude, high=amplitude, size=stop_sample - start_sample
                )
                self._param_dict[SPC_DATA_AVAIL_USER_POS] = start_sample * bytes_per_sample
                self._param_dict[SPC_DATA_AVAIL_USER_LEN] = (stop_sample - start_sample) * bytes_per_sample
            sample_count += notify_size_in_samples
            self._param_dict[TRANSFER_CHUNK_COUNTER] += 1

            sleep(1 / notify_sizes_per_second)


def mock_waveform_source_factory(
    acquisition_mode: AcquisitionMode,
    param_dict: Dict[int, int],
    notify_size_in_pages: int = 0,
) -> MockWaveformSource:
    if acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
        return MultiFIFOModeMockWaveformSource(param_dict, notify_size_in_pages)
    elif AcquisitionMode.SPC_REC_STD_SINGLE:
        return SingleModeMockWaveformSource(param_dict)
    else:
        raise NotImplementedError(f"Mock waveform source not yet implemented for {acquisition_mode} acquisition mode.")
