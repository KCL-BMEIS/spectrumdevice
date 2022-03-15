import datetime

from numpy import uint64

from spectrum_gmbh.regs import SPC_TIMESTAMP_CMD
from spectrumdevice.devices.spectrum_timestamper import Timestamper
from spectrumdevice.settings.timestamps import TimestampMode
from spectrumdevice.spectrum_wrapper import DEVICE_HANDLE_TYPE

BYTES_PER_TIMESTAMP = 16
BYTES_PER_TIMESTAMP_BUFFER_ELEMENT = 8
TIMESTAMP_BUFFER_ELEMENT_D_TYPE = uint64
ON_BOARD_TIMESTAMP_MEMORY_SIZE_BYTES = 16384


class MockTimestamper(Timestamper):
    def _configure_parent_device(self, handle: DEVICE_HANDLE_TYPE) -> None:
        """This is a mock class, so don't need to set transfer buffer on hardware. Replaces method in Timestamper."""
        # Enable standard timestamp mode (timestamps are in seconds relative to the reference time)
        self._parent_device.write_to_spectrum_device_register(SPC_TIMESTAMP_CMD, TimestampMode.STANDARD.value)

    def _read_ref_time_from_device(self) -> datetime.datetime:
        return datetime.datetime.now()

    def get_timestamp(self) -> datetime.datetime:
        return datetime.datetime.now()
