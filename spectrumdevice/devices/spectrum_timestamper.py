import struct
from abc import ABC
from copy import copy
from datetime import datetime, timedelta
from time import sleep
from typing import List, Tuple

from numpy import array, concatenate, floor

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

MAX_POLL_COUNT = 3000


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

        self._ref_time = self._read_ref_time_from_device()
        self._sampling_rate_hz = self._parent_device.sample_rate_in_hz

    def _configure_parent_device(self, handle: DEVICE_HANDLE_TYPE) -> None:
        set_transfer_buffer(handle, self._transfer_buffer)
        # Enable standard timestamp mode (timestamps are in seconds relative to the reference time)
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, TimestampMode.STANDARD.value)
        # Set the local PC time to the reference time register on the card
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, SPC_TS_RESET)
        if self._parent_device.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
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

    def get_timestamps(self) -> List[datetime]:
        poll_count = 0
        n_kept_bytes = 0

        if self._parent_device.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:

            kept_bytes = []
            while (n_kept_bytes < self._expected_timestamp_bytes_per_frame) and (poll_count < MAX_POLL_COUNT):

                print(f"\n NEW POLL STARTING (poll count {poll_count}) \n")
                print("Transfer buffer contents at start of poll:")
                print(self._transfer_buffer.data_array)

                start_pos_int_bytes, num_available_bytes = self._transfer_timestamps_to_transfer_buffer()
                sleep(10e-3)
                print(f"The card has inserted {num_available_bytes} bytes into the buffer"
                      f" at position {start_pos_int_bytes}")

                if (start_pos_int_bytes + num_available_bytes) >= self._transfer_buffer.data_array_length_in_bytes:
                    print("(new bytes wrapping around to beginning of buffer)")
                    n_bytes_to_keep = self._transfer_buffer.data_array_length_in_bytes - start_pos_int_bytes
                else:
                    n_bytes_to_keep = num_available_bytes

                if n_bytes_to_keep > 0:
                    if n_bytes_to_keep > self._expected_timestamp_bytes_per_frame:
                        n_bytes_to_keep = self._expected_timestamp_bytes_per_frame
                    print(f"*** Keeping {n_bytes_to_keep} bytes starting at position {start_pos_int_bytes}:")
                    kept_bytes += list(copy(
                        self._transfer_buffer.data_array[start_pos_int_bytes:start_pos_int_bytes+n_bytes_to_keep]))
                    print(f"{kept_bytes[-n_bytes_to_keep:]}")
                    n_kept_bytes += n_bytes_to_keep
                    self._mark_transfer_buffer_elements_as_free(n_bytes_to_keep)

                print("Transfer buffer contents at end of poll:")
                print(self._transfer_buffer.data_array)
                poll_count += 1

            if n_kept_bytes < self._expected_timestamp_bytes_per_frame:
                raise SpectrumTimestampsPollingTimeout()
        else:
            kept_bytes = self._transfer_buffer.copy_contents()

        bigendian = struct.unpack(">2Q", struct.pack(f">{len(kept_bytes)}B", *kept_bytes))
        littleendian = struct.unpack("<2Q", struct.pack(f"<{len(kept_bytes)}B", *kept_bytes))

        print('-------------------')
        print(f'GOT BYTES! {kept_bytes}')
        print(f'ENCODED BIGENDIAN: {bigendian}')
        print(f'ENCODED LITTLEENDIAN: {littleendian}')
        print('-------------------')

        timestamps_in_seconds_since_ref = array(
            [[timedelta(seconds=float(ts) / self._sampling_rate_hz) for ts in littleendian][0]]
        )
        timestamps_in_datetime = self._ref_time + timestamps_in_seconds_since_ref

        print('REF TIME:')
        print(self._ref_time)

        return list(timestamps_in_datetime)
