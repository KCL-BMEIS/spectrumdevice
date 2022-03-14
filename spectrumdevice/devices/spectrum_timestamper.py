import struct
import time
from abc import ABC
from copy import copy
from datetime import datetime, timedelta
from typing import Tuple

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
    M2CMD_CARD_WRITESETUP,
)
from spectrumdevice.devices.spectrum_interface import SpectrumDeviceInterface
from spectrumdevice.exceptions import (
    SpectrumTimestampsPollingTimeout,
)
from spectrumdevice.settings import TriggerSource
from spectrumdevice.settings.timestamps import spectrum_ref_time_to_datetime, TimestampMode
from spectrumdevice.settings.transfer_buffer import CardToPCTimestampTransferBuffer, set_transfer_buffer
from spectrumdevice.spectrum_wrapper import DEVICE_HANDLE_TYPE

MAX_POLL_COUNT = 50


class Timestamper(ABC):
    def __init__(
        self,
        parent_device: SpectrumDeviceInterface,
        parent_device_handle: DEVICE_HANDLE_TYPE,
        n_timestamps_per_frame: int,
    ):
        self._parent_device = parent_device
        self._transfer_buffer = CardToPCTimestampTransferBuffer(n_timestamps_per_frame)
        self._expected_timestamp_bytes_per_frame = 16
        self._n_timestamps_per_frame = n_timestamps_per_frame

        self._configure_parent_device(parent_device_handle)

        self._ref_time = self._read_ref_time_from_device()
        self._sampling_rate_hz = self._parent_device.sample_rate_in_hz

    def _configure_parent_device(self, handle: DEVICE_HANDLE_TYPE) -> None:
        set_transfer_buffer(handle, self._transfer_buffer)
        # Enable standard timestamp mode (timestamps are in seconds relative to the reference time)
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, TimestampMode.STANDARD.value)

        self._parent_device.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_WRITESETUP)
        # Set the local PC time to the reference time register on the card
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, SPC_TS_RESET)

        # Enable polling mode so we can get the timestamps without waiting for a notification
        self._parent_device.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_EXTRA_POLL)

    def _read_ref_time_from_device(self) -> datetime:
        start_time = self._parent_device.read_spectrum_device_register(SPC_TIMESTAMP_STARTTIME)
        start_date = self._parent_device.read_spectrum_device_register(SPC_TIMESTAMP_STARTDATE)
        return spectrum_ref_time_to_datetime(start_time, start_date)

    def _transfer_timestamps_to_transfer_buffer(self) -> Tuple[int, int]:
        num_available_bytes = self._parent_device.read_spectrum_device_register(SPC_TS_AVAIL_USER_LEN)
        start_pos = self._parent_device.read_spectrum_device_register(SPC_TS_AVAIL_USER_POS)
        return start_pos, num_available_bytes

    def _mark_transfer_buffer_elements_as_free(self, num_available_bytes: int) -> None:
        self._parent_device.write_to_spectrum_device_register(SPC_TS_AVAIL_CARD_LEN, num_available_bytes)

    def get_timestamp(self) -> datetime:

        trigger_source = self._parent_device.trigger_sources
        if len(trigger_source) == 1 and trigger_source[0] == TriggerSource.SPC_TMASK_SOFTWARE:
            return datetime.now()

        poll_count = 0
        n_kept_bytes = 0
        kept_bytes = []

        while (n_kept_bytes < self._expected_timestamp_bytes_per_frame) and (poll_count < MAX_POLL_COUNT):

            n_bytes_not_yet_received = self._expected_timestamp_bytes_per_frame - n_kept_bytes
            num_available_bytes = self._parent_device.read_spectrum_device_register(SPC_TS_AVAIL_USER_LEN)
            start_pos_int_bytes = self._parent_device.read_spectrum_device_register(SPC_TS_AVAIL_USER_POS)

            # don't go beyond the size of the ts data buffer
            if (start_pos_int_bytes + num_available_bytes) >= self._transfer_buffer.data_array_length_in_bytes:
                num_available_bytes = self._transfer_buffer.data_array_length_in_bytes - start_pos_int_bytes

            if 0 < num_available_bytes <= n_bytes_not_yet_received:
                n_bytes_to_keep = num_available_bytes
            else:
                n_bytes_to_keep = n_bytes_not_yet_received

            if n_bytes_to_keep > 0:
                kept_bytes += list(
                    copy(self._transfer_buffer.data_array[start_pos_int_bytes : start_pos_int_bytes + n_bytes_to_keep])
                )
                n_kept_bytes += len(kept_bytes)
                self._mark_transfer_buffer_elements_as_free(len(kept_bytes))

            poll_count += 1

        if n_kept_bytes < self._expected_timestamp_bytes_per_frame:
            raise SpectrumTimestampsPollingTimeout()

        timestamp_in_samples = struct.unpack("<2Q", struct.pack(f"<{len(kept_bytes)}B", *kept_bytes))[0]
        timestamp_in_seconds_since_ref = timedelta(seconds=float(timestamp_in_samples) / self._sampling_rate_hz)

        timestamp_in_datetime = self._ref_time + timestamp_in_seconds_since_ref

        return timestamp_in_datetime
