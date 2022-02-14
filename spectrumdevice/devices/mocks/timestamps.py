import time
from abc import ABC, abstractmethod
from threading import Lock, Event
from time import monotonic, sleep

from numpy import ones, zeros, concatenate, uint64, ndarray

from spectrumdevice.devices.mocks.circular_buffer import _write_to_circular_buffer, MockCircularBufferOverrunError
from spectrumdevice.exceptions import SpectrumNotEnoughRoomInTimestampsBufferError
from spectrumdevice.settings.transfer_buffer import CardToPCTimestampTransferBuffer


BYTES_PER_TIMESTAMP = 16
BYTES_PER_TIMESTAMP_BUFFER_ELEMENT = 8
TIMESTAMP_BUFFER_ELEMENT_D_TYPE = uint64
ON_BOARD_TIMESTAMP_MEMORY_SIZE_BYTES = 16384


class MockTimestampSource(ABC):
    """Simulates the transfer of timestamps into a timestamp transfer buffer in polling mode."""
    def __init__(self, transfer_buffer: CardToPCTimestampTransferBuffer, sample_rate_hz: float):
        self._on_device_memory_lock = Lock()
        self._buffer_next_write_position_counter_in_bytes = 0
        self._transfer_buffer = transfer_buffer
        self._transfer_buffer_elements_free_status = ones(len(self._transfer_buffer.data_array), dtype=bool)

        self._reference_time = time.monotonic()
        self._sample_rate = sample_rate_hz

        on_board_array_size = int(ON_BOARD_TIMESTAMP_MEMORY_SIZE_BYTES / BYTES_PER_TIMESTAMP_BUFFER_ELEMENT)
        self._on_device_memory = zeros(on_board_array_size, dtype=TIMESTAMP_BUFFER_ELEMENT_D_TYPE)
        self._device_memory_next_write_position_counter_in_elements = 0
        self._on_device_memory_free_status = ones(on_board_array_size, dtype=bool)

        self._last_returned_start_pos_in_bytes = 0
        self._last_returned_n_available_bytes = 0

    @abstractmethod
    def __call__(self, stop_flag: Event, frame_rate: float, timestamps_per_frame: int):
        raise NotImplementedError()

    def mark_transfer_buffer_elements_as_free(self, num_elements: int):

        start_pos_in_elements = int(self._last_returned_start_pos_in_bytes / BYTES_PER_TIMESTAMP_BUFFER_ELEMENT)
        self._transfer_buffer_elements_free_status[start_pos_in_elements:start_pos_in_elements + num_elements] = True

    def transfer_timestamps_to_buffer(self) -> (int, int):

        start_write_index = int(self._buffer_next_write_position_counter_in_bytes / BYTES_PER_TIMESTAMP_BUFFER_ELEMENT)

        try:
            with self._on_device_memory_lock:
                print("Timestamps to transfer")
                print(self._on_device_memory[[not s for s in self._on_device_memory_free_status]])
                last_index_wrtn = _write_to_circular_buffer(
                    self._transfer_buffer.data_array,
                    self._transfer_buffer_elements_free_status,
                    self._on_device_memory,
                    start_write_index,
                    self._on_device_memory_free_status
                )
                print("Buffer array after transfer")
                print(self._transfer_buffer.data_array)
                print(self._transfer_buffer_elements_free_status)
                print(f"last index written: {last_index_wrtn}")

        except MockCircularBufferOverrunError:
            raise SpectrumNotEnoughRoomInTimestampsBufferError()

        self._buffer_next_write_position_counter_in_bytes = (last_index_wrtn + 1) * BYTES_PER_TIMESTAMP_BUFFER_ELEMENT
        num_occupied_elements_in_buffer = len(self._transfer_buffer.data_array[
                                                  [not s for s in self._transfer_buffer_elements_free_status]
                                              ])

        self._last_returned_n_available_bytes = num_occupied_elements_in_buffer * BYTES_PER_TIMESTAMP_BUFFER_ELEMENT
        self._last_returned_start_pos_in_bytes = start_write_index * BYTES_PER_TIMESTAMP_BUFFER_ELEMENT
        return self._last_returned_start_pos_in_bytes, self._last_returned_n_available_bytes


class SingleModeMockTimestampSource(MockTimestampSource):
    def __call__(self, stop_flag: Event, frame_rate: float, timestamps_per_frame: int):
        start_time = monotonic()
        while not stop_flag.is_set() and ((monotonic() - start_time) < (1 / frame_rate)):
            sleep(0.001)
        if not stop_flag.is_set():
            timestamps_128bit = _generate_new_timestamps(self._reference_time, self._sample_rate, timestamps_per_frame)
            with self._on_device_memory_lock:
                last_position_written_to = _write_to_circular_buffer(
                    self._on_device_memory,
                    self._on_device_memory_free_status,
                    timestamps_128bit,
                    self._device_memory_next_write_position_counter_in_elements,
                )
            self._device_memory_next_write_position_counter_in_elements = last_position_written_to + 1


class FIFOModeMockTimestampSource(MockTimestampSource):
    def __call__(self, stop_flag: Event, frame_rate: float, timestamps_per_frame: int):
        while not stop_flag.is_set():
            timestamps_128bit = _generate_new_timestamps(self._reference_time, self._sample_rate, timestamps_per_frame)
            with self._on_device_memory_lock:
                last_position_written_to = _write_to_circular_buffer(
                    self._on_device_memory,
                    self._on_device_memory_free_status,
                    timestamps_128bit,
                    self._device_memory_next_write_position_counter_in_elements,
                )
                self._device_memory_next_write_position_counter_in_elements = last_position_written_to + 1
                sleep(1 / frame_rate)


def _generate_new_timestamps(reference_time_s: float, sample_rate_hz: float, n_timestamps: int) -> ndarray:
    timestamp_in_samples = round((time.monotonic() - reference_time_s) * sample_rate_hz)
    timestamps = ones(n_timestamps, dtype=TIMESTAMP_BUFFER_ELEMENT_D_TYPE) \
                 * TIMESTAMP_BUFFER_ELEMENT_D_TYPE(timestamp_in_samples)
    return concatenate([[TIMESTAMP_BUFFER_ELEMENT_D_TYPE(0), t] for t in timestamps])
