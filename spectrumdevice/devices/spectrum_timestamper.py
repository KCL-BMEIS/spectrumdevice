from abc import ABC
from datetime import datetime, timedelta
from typing import List, Tuple

from numpy import array

from spectrum_gmbh.regs import (
    SPC_TIMESTAMP_CMD,
    SPC_TS_RESET,
    SPC_M2CMD,
    SPC_TS_AVAIL_USER_LEN,
    SPC_TS_AVAIL_CARD_LEN,
    SPC_TIMESTAMP_STARTTIME,
    SPC_TIMESTAMP_STARTDATE,
    M2CMD_EXTRA_POLL,
    SPC_TS_AVAIL_USER_POS,
)
from spectrumdevice.devices.spectrum_interface import SpectrumDeviceInterface
from spectrumdevice.exceptions import (
    SpectrumNotEnoughRoomInTimestampsBufferError,
    SpectrumTimestampsPollingTimeout,
)
from spectrumdevice.settings import AcquisitionMode
from spectrumdevice.settings.timestamps import spectrum_ref_time_to_datetime, TimestampMode
from spectrumdevice.settings.transfer_buffer import CardToPCTimestampTransferBuffer, set_transfer_buffer
from spectrumdevice.spectrum_wrapper import DEVICE_HANDLE_TYPE

MAX_POLL_COUNT = 100


class Timestamper(ABC):
    def __init__(
        self,
        parent_device: SpectrumDeviceInterface,
        parent_device_handle: DEVICE_HANDLE_TYPE,
        n_timestamps_per_frame: int,
    ):
        self._parent_device = parent_device
        self._transfer_buffer = CardToPCTimestampTransferBuffer(n_timestamps_per_frame)
        self._expected_timestamp_bytes_per_frame = self._transfer_buffer.data_array_length_in_bytes
        self._n_timestamps_per_frame = n_timestamps_per_frame

        self._configure_parent_device(parent_device_handle)

        if self._parent_device.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            # Enable polling mode so we can get the timestamps without waiting for a notification
            self._parent_device.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_EXTRA_POLL)
        self._ref_time = self._get_ref_time()
        self._sampling_rate_hz = self._parent_device.sample_rate_in_hz

    def _configure_parent_device(self, handle: DEVICE_HANDLE_TYPE) -> None:
        set_transfer_buffer(handle, self._transfer_buffer)
        # Set the local PC time to the reference time register on the card
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, SPC_TS_RESET)
        # Enable standard timestamp mode (timestamps are in seconds relative to the reference time)
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, TimestampMode.STANDARD.value)

    def _get_ref_time(self) -> datetime:
        start_time = self._parent_device.read_spectrum_device_register(SPC_TIMESTAMP_STARTTIME)
        start_date = self._parent_device.read_spectrum_device_register(SPC_TIMESTAMP_STARTDATE)
        return spectrum_ref_time_to_datetime(start_time, start_date)

    def _transfer_timestamps_to_transfer_buffer(self) -> Tuple[int, int]:
        num_available_bytes = self._parent_device.read_spectrum_device_register(SPC_TS_AVAIL_USER_LEN)
        start_pos = self._parent_device.read_spectrum_device_register(SPC_TS_AVAIL_USER_POS)
        return start_pos, num_available_bytes

    def _mark_transfer_buffer_elements_as_free(self, num_available_bytes: int) -> None:
        self._parent_device.write_to_spectrum_device_register(SPC_TS_AVAIL_CARD_LEN, num_available_bytes)

    def get_timestamps(self) -> List[datetime]:
        num_available_bytes = 0
        poll_count = 0

        if self._parent_device.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:

            while (num_available_bytes < self._expected_timestamp_bytes_per_frame) and (poll_count < MAX_POLL_COUNT):
                start_pos, num_available_bytes = self._transfer_timestamps_to_transfer_buffer()
                print(f"\nStart pos is {start_pos} and there are {num_available_bytes} available")
                if start_pos != 0 or num_available_bytes > self._expected_timestamp_bytes_per_frame:
                    raise SpectrumNotEnoughRoomInTimestampsBufferError()
                poll_count += 1

            if num_available_bytes < self._expected_timestamp_bytes_per_frame:
                raise SpectrumTimestampsPollingTimeout()

            timestamps_in_samples = self._transfer_buffer.copy_contents()
            self._mark_transfer_buffer_elements_as_free(num_available_bytes)
            print(
                f"\nPolled {poll_count} times, transferred {num_available_bytes} bytes "
                f"(expected {self._expected_timestamp_bytes_per_frame} bytes)."
            )

        else:
            timestamps_in_samples = self._transfer_buffer.copy_contents()

        timestamps_in_seconds_since_ref = array(
            [timedelta(seconds=ts / self._sampling_rate_hz) for ts in timestamps_in_samples]
        )
        try:
            timestamps_in_datetime = self._ref_time + timestamps_in_seconds_since_ref
        except OverflowError as e:
            print(timestamps_in_seconds_since_ref)
            raise e

        return list(timestamps_in_datetime)
