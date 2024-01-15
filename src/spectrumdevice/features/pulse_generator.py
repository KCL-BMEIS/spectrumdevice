from spectrumdevice.devices.abstract_device.interfaces import SpectrumIOLineInterface
from spectrumdevice.settings import IOLineMode


class PulseGenerator:
    def __init__(self, parent: SpectrumIOLineInterface):
        self._parent_io_line = parent

    @property
    def enabled(self) -> bool:
        self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_ENABLE)

    @property
    def output_enabled(self) -> bool:
        channel_is_in_pulser_mode = self._parent_io_line.mode == IOLineMode.SPCM_XMODE_PULSEGEN
        pulser_is_enabled = self._parent_io_line.read_parent_device_register()
        return self._parent_io_line.mode == IOLineMode.SPCM_XMODE_PULSEGEN

    def set_output_enabled(self, enabled: bool):
        self._parent_io_line.set_mode(IOLineMode.SPCM_XMODE_PULSEGEN)


