from abc import ABC, abstractmethod

from spectrumdevice.devices.abstract_device import AbstractSpectrumChannel
from spectrumdevice.devices.abstract_device.interfaces import SpectrumIOLineInterface
from spectrumdevice.settings import IOLineMode
from spectrumdevice.settings.io_lines import IO_LINE_MODE_COMMANDS, SpectrumIOLineName


class AbstractSpectrumIOLine(SpectrumIOLineInterface, AbstractSpectrumChannel[SpectrumIOLineName], ABC):
    """Partially implemented abstract superclass contain code common for controlling an individual IO Line of all
    spectrum devices."""

    @property
    def _name_prefix(self) -> str:
        return "X"

    def _make_name(self, channel_number: int) -> SpectrumIOLineName:
        return SpectrumIOLineName[f"{self._name_prefix}{channel_number}"]

    @abstractmethod
    def _get_io_line_mode_settings_mask(self, mode: IOLineMode) -> int:
        raise NotImplementedError

    @property
    def mode(self) -> IOLineMode:
        # todo: this may contain dig out settings bits, so needs a decode function that ignores those bits
        return IOLineMode(self._parent_device.read_spectrum_device_register(IO_LINE_MODE_COMMANDS[self._number]))

    def set_mode(self, mode: IOLineMode) -> None:
        value_to_write = self._get_io_line_mode_settings_mask(mode) | mode.value
        self._parent_device.write_to_spectrum_device_register(IO_LINE_MODE_COMMANDS[self._number], value_to_write)
