import datetime
import time
from abc import ABC, abstractmethod
from functools import partial
from threading import Lock, Event
from time import monotonic, sleep
from typing import Tuple, Optional, Callable

from numpy import ones, zeros, concatenate, uint64, ndarray, bool_
from numpy.typing import NDArray

from spectrum_gmbh.regs import SPC_TIMESTAMP_CMD, SPC_TS_RESET
from spectrumdevice.devices.mocks.circular_buffer import _write_to_circular_buffer, MockCircularBufferOverrunError
from spectrumdevice.devices.spectrum_interface import SpectrumDeviceInterface
from spectrumdevice.devices.spectrum_timestamper import Timestamper
from spectrumdevice.exceptions import SpectrumNotEnoughRoomInTimestampsBufferError
from spectrumdevice.settings import AcquisitionMode
from spectrumdevice.settings.timestamps import TimestampMode
from spectrumdevice.settings.transfer_buffer import CardToPCTimestampTransferBuffer
from spectrumdevice.spectrum_wrapper import DEVICE_HANDLE_TYPE

BYTES_PER_TIMESTAMP = 16
BYTES_PER_TIMESTAMP_BUFFER_ELEMENT = 8
TIMESTAMP_BUFFER_ELEMENT_D_TYPE = uint64
ON_BOARD_TIMESTAMP_MEMORY_SIZE_BYTES = 16384


class MockTimestamper(Timestamper):
    def __init__(
        self,
        parent_device: SpectrumDeviceInterface,
        parent_device_handle: DEVICE_HANDLE_TYPE,
        n_timestamps_per_frame: int,
    ):

        if parent_device.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            self._timestamp_source: MockTimestampSource = FIFOModeMockTimestampSource(parent_device.sample_rate_in_hz)
        elif parent_device.acquisition_mode == AcquisitionMode.SPC_REC_STD_SINGLE:
            self._timestamp_source = SingleModeMockTimestampSource(parent_device.sample_rate_in_hz)
        else:
            raise ValueError(f"Unsupported mode: {parent_device.acquisition_mode}")

        super().__init__(parent_device, parent_device_handle, n_timestamps_per_frame)
        self._timestamp_source.set_transfer_buffer(self._transfer_buffer)

    def mock_source_function_factory(self, stop_flag: Event, frame_rate: float, timestamps_per_frame: int) -> Callable:
        return partial(self._timestamp_source, stop_flag, frame_rate, timestamps_per_frame)

    def _configure_parent_device(self, handle: DEVICE_HANDLE_TYPE) -> None:
        """This is a mock class, so don't need to set transfer buffer on hardware. Replaces method in Timestamper."""
        # Set the local PC time to the reference time register on the card
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, SPC_TS_RESET)
        # Enable standard timestamp mode (timestamps are in seconds relative to the reference time)
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, TimestampMode.STANDARD.value)

    def _read_ref_time_from_device(self) -> datetime.datetime:
        """Reads reference time from the mock timestamp source, instead of hardware."""
        return self._timestamp_source.ref_time

    def _transfer_timestamps_to_transfer_buffer(self) -> Tuple[int, int]:
        """Use the mock timestamp source to generate timestamps and put them in the transfer buffer."""
        start_pos, n_bytes = self._timestamp_source.transfer_timestamps_to_buffer()
        return start_pos, n_bytes

    def _mark_transfer_buffer_elements_as_free(self, num_available_bytes: int) -> None:
        """Tell the mock timestamp source that timestamps in the buffer have been read."""
        num_elements = int(round(num_available_bytes / BYTES_PER_TIMESTAMP_BUFFER_ELEMENT))
        self._timestamp_source.mark_transfer_buffer_elements_as_free(num_elements)


class MockTimestampSource(ABC):
    """Simulates the transfer of timestamps into a timestamp transfer buffer in polling mode."""

    def __init__(self, sample_rate_hz: float):
        self._on_device_memory_lock = Lock()
        self._buffer_next_write_position_counter_in_bytes = 0

        self._reference_datetime = datetime.datetime.now()
        self._reference_time = time.monotonic()
        self._sample_rate = sample_rate_hz

        on_board_array_size = int(ON_BOARD_TIMESTAMP_MEMORY_SIZE_BYTES / BYTES_PER_TIMESTAMP_BUFFER_ELEMENT)
        self._on_device_memory = zeros(on_board_array_size, dtype=TIMESTAMP_BUFFER_ELEMENT_D_TYPE)
        self._device_memory_next_write_position_counter_in_elements = 0
        self._on_device_memory_free_status = ones(on_board_array_size, dtype=bool)

        self._last_returned_start_pos_in_bytes = 0
        self._last_returned_n_available_bytes = 0

        self._transfer_buffer: Optional[CardToPCTimestampTransferBuffer] = None
        self._transfer_buffer_elements_free_status: Optional[NDArray[bool_]] = None

    def set_transfer_buffer(self, transfer_buffer: CardToPCTimestampTransferBuffer) -> None:
        self._transfer_buffer = transfer_buffer
        self._transfer_buffer_elements_free_status = ones(len(self._transfer_buffer.data_array), dtype=bool)

    @abstractmethod
    def __call__(self, stop_flag: Event, frame_rate: float, timestamps_per_frame: int) -> None:
        raise NotImplementedError()

    @property
    def ref_time(self) -> datetime.datetime:
        return self._reference_datetime

    def mark_transfer_buffer_elements_as_free(self, num_elements: int) -> None:

        start_pos_in_elements = int(self._last_returned_start_pos_in_bytes / BYTES_PER_TIMESTAMP_BUFFER_ELEMENT)
        if self._transfer_buffer_elements_free_status is not None:
            self._transfer_buffer_elements_free_status[
                start_pos_in_elements : start_pos_in_elements + num_elements
            ] = True

    def transfer_timestamps_to_buffer(self) -> Tuple[int, int]:

        start_write_index = int(self._buffer_next_write_position_counter_in_bytes / BYTES_PER_TIMESTAMP_BUFFER_ELEMENT)
        if self._transfer_buffer is None or self._transfer_buffer_elements_free_status is None:
            raise ValueError("Timestamp transfer buffer has not been created.")
        else:
            try:
                with self._on_device_memory_lock:
                    write_head = _write_to_circular_buffer(
                        self._transfer_buffer.data_array,
                        self._transfer_buffer_elements_free_status,
                        self._on_device_memory,
                        start_write_index,
                        self._on_device_memory_free_status,
                    )
            except MockCircularBufferOverrunError:
                raise SpectrumNotEnoughRoomInTimestampsBufferError()

        self._buffer_next_write_position_counter_in_bytes = (
            write_head.next_write_pos * BYTES_PER_TIMESTAMP_BUFFER_ELEMENT
        )
        num_occupied_elements_in_buffer = len(
            self._transfer_buffer.data_array[[not s for s in self._transfer_buffer_elements_free_status]]
        )

        self._last_returned_n_available_bytes = num_occupied_elements_in_buffer * BYTES_PER_TIMESTAMP_BUFFER_ELEMENT
        self._last_returned_start_pos_in_bytes = start_write_index * BYTES_PER_TIMESTAMP_BUFFER_ELEMENT
        return self._last_returned_start_pos_in_bytes, self._last_returned_n_available_bytes


class SingleModeMockTimestampSource(MockTimestampSource):
    def __call__(self, stop_flag: Event, frame_rate: float, timestamps_per_frame: int) -> None:
        start_time = monotonic()
        while not stop_flag.is_set() and ((monotonic() - start_time) < (1 / frame_rate)):
            sleep(0.001)
        if not stop_flag.is_set():
            timestamps_128bit = _generate_new_timestamps(self._reference_time, self._sample_rate, timestamps_per_frame)
            with self._on_device_memory_lock:
                write_head = _write_to_circular_buffer(
                    self._on_device_memory,
                    self._on_device_memory_free_status,
                    timestamps_128bit,
                    self._device_memory_next_write_position_counter_in_elements,
                )
            self._device_memory_next_write_position_counter_in_elements = write_head.next_write_pos


class FIFOModeMockTimestampSource(MockTimestampSource):
    def __call__(self, stop_flag: Event, frame_rate: float, timestamps_per_frame: int) -> None:
        while not stop_flag.is_set():
            timestamps_128bit = _generate_new_timestamps(self._reference_time, self._sample_rate, timestamps_per_frame)
            with self._on_device_memory_lock:
                write_head = _write_to_circular_buffer(
                    self._on_device_memory,
                    self._on_device_memory_free_status,
                    timestamps_128bit,
                    self._device_memory_next_write_position_counter_in_elements,
                )
            self._device_memory_next_write_position_counter_in_elements = write_head.next_write_pos
            sleep(1 / frame_rate)


def _generate_new_timestamps(reference_time_s: float, sample_rate_hz: float, n_timestamps: int) -> ndarray:
    timestamp_in_samples = round((time.monotonic() - reference_time_s) * sample_rate_hz)
    timestamps = ones(n_timestamps, dtype=TIMESTAMP_BUFFER_ELEMENT_D_TYPE) * TIMESTAMP_BUFFER_ELEMENT_D_TYPE(
        timestamp_in_samples
    )
    return concatenate([[TIMESTAMP_BUFFER_ELEMENT_D_TYPE(0), t] for t in timestamps])