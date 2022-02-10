from abc import ABC
from copy import copy
from datetime import datetime, timedelta
from typing import List

from numpy import array

from spectrum_gmbh.regs import (
    SPC_TIMESTAMP_CMD,
    SPC_TS_RESET,
    M2CMD_EXTRA_WAITDMA,
    SPC_M2CMD,
    SPC_TS_AVAIL_USER_LEN,
    SPC_TS_AVAIL_CARD_LEN,
    SPC_TIMESTAMP_STARTTIME,
    SPC_TIMESTAMP_STARTDATE,
)
from spectrumdevice.devices.spectrum_interface import SpectrumDeviceInterface
from spectrumdevice.settings import AcquisitionMode
from spectrumdevice.settings.timestamps import spectrum_ref_time_to_datetime, TimestampMode
from spectrumdevice.settings.transfer_buffer import CardToPCTimestampTransferBuffer, set_transfer_buffer
from spectrumdevice.spectrum_wrapper import DEVICE_HANDLE_TYPE


class Timestamper(ABC):
    def __init__(
        self,
        parent_device: SpectrumDeviceInterface,
        parent_device_handle: DEVICE_HANDLE_TYPE,
        n_timestamps_per_frame: int,
    ):
        self._parent_device = parent_device
        self._transfer_buffer = CardToPCTimestampTransferBuffer(n_timestamps_per_frame)
        set_transfer_buffer(parent_device_handle, self._transfer_buffer)
        # Set the local PC time to the reference time register on the card
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, SPC_TS_RESET)
        # Enable standard timestamp mode (timestamps are in seconds relative to the reference time)
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, TimestampMode.STANDARD.value)
        self._ref_time = self._get_ref_time()
        self._sampling_rate_hz = self._parent_device.sample_rate_in_hz

    def _get_ref_time(self) -> datetime:
        start_time = self._parent_device.read_spectrum_device_register(SPC_TIMESTAMP_STARTTIME)
        start_date = self._parent_device.read_spectrum_device_register(SPC_TIMESTAMP_STARTDATE)
        return spectrum_ref_time_to_datetime(start_time, start_date)

    def wait_for_transfer_to_complete(self) -> None:
        self._parent_device.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_EXTRA_WAITDMA)

    def get_timestamps(self) -> List[datetime]:
        if self._parent_device.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            self.wait_for_transfer_to_complete()
            num_available_bytes = self._parent_device.read_spectrum_device_register(SPC_TS_AVAIL_USER_LEN)
        else:
            num_available_bytes = 0

        timestamps_in_samples = copy(self._transfer_buffer.data_array)
        if self._parent_device.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            self._parent_device.write_to_spectrum_device_register(SPC_TS_AVAIL_CARD_LEN, num_available_bytes)

        timestamps_in_seconds_since_ref = array(
            [timedelta(seconds=ts / self._sampling_rate_hz) for ts in timestamps_in_samples]
        )
        timestamps_in_datetime = self._ref_time + timestamps_in_seconds_since_ref

        return list(timestamps_in_datetime)
