from abc import ABC, abstractmethod
from threading import Event, Lock
from time import monotonic, sleep

from numpy import ndarray
from numpy.random import uniform

from spectrumdevice.settings import AcquisitionMode


class MockWaveformSource(ABC):
    """Interface for a mock noise waveform source. Implementations are intended to be called in their own thread.
    When called, `MockWaveformSource` implementations will fill a provided buffer with noise samples."""

    @abstractmethod
    def __call__(
        self, stop_flag: Event, frame_rate: float, amplitude: float, on_device_buffer: ndarray, buffer_lock: Lock
    ) -> None:
        raise NotImplementedError()


class SingleModeMockWaveformSource(MockWaveformSource):
    def __call__(
        self, stop_flag: Event, frame_rate: float, amplitude: float, on_device_buffer: ndarray, buffer_lock: Lock
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
        while not stop_flag.is_set() and ((monotonic() - start_time) < (1 / frame_rate)):
            sleep(0.001)
        if not stop_flag.is_set():
            with buffer_lock:
                on_device_buffer[:] = uniform(low=-1 * amplitude, high=amplitude, size=len(on_device_buffer))


class MultiFIFOModeMockWaveformSource(MockWaveformSource):
    def __call__(
        self, stop_flag: Event, frame_rate: float, amplitude: float, on_device_buffer: ndarray, buffer_lock: Lock
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
        while not stop_flag.is_set():
            with buffer_lock:
                on_device_buffer[:] = uniform(low=-1 * amplitude, high=amplitude, size=len(on_device_buffer))
                sleep(1 / frame_rate)


def mock_waveform_source_factory(acquisition_mode: AcquisitionMode) -> MockWaveformSource:
    if acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
        return MultiFIFOModeMockWaveformSource()
    elif AcquisitionMode.SPC_REC_STD_SINGLE:
        return SingleModeMockWaveformSource()
    else:
        raise NotImplementedError(f"Mock waveform source not yet implemented for {acquisition_mode} acquisition mode.")
