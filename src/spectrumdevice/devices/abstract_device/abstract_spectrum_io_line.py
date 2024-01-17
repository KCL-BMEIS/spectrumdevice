from abc import ABC, abstractmethod
from typing import Any, Optional

from spectrumdevice.devices.abstract_device import AbstractSpectrumChannel
from spectrumdevice.devices.abstract_device.channel_interfaces import SpectrumIOLineInterface
from spectrumdevice.exceptions import SpectrumFeatureNotSupportedByCard
from spectrumdevice.features.pulse_generator.pulse_generator import PulseGenerator
from spectrumdevice.features.pulse_generator.interfaces import PulseGeneratorInterface
from spectrumdevice.settings import IOLineMode
from spectrumdevice.settings.io_lines import IO_LINE_MODE_COMMANDS, SpectrumIOLineName, decode_enabled_io_line_mode


class AbstractSpectrumIOLine(SpectrumIOLineInterface, AbstractSpectrumChannel[SpectrumIOLineName], ABC):
    """Partially implemented abstract superclass contain code common for controlling an individual IO Line of all
    spectrum devices."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        try:
            self._pulse_generator: Optional[PulseGenerator] = PulseGenerator(parent=self)
        except SpectrumFeatureNotSupportedByCard:
            self._pulse_generator = None

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
        return decode_enabled_io_line_mode(
            self._parent_device.read_spectrum_device_register(IO_LINE_MODE_COMMANDS[self._number])
        )

    def set_mode(self, mode: IOLineMode) -> None:
        value_to_write = self._get_io_line_mode_settings_mask(mode) | mode.value
        self._parent_device.write_to_spectrum_device_register(IO_LINE_MODE_COMMANDS[self._number], value_to_write)

    @property
    def pulse_generator(self) -> PulseGeneratorInterface:
        """Gets the IO line's pulse generator."""
        if self._pulse_generator is not None:
            return self._pulse_generator
        else:
            raise SpectrumFeatureNotSupportedByCard(
                call_description=self.__str__() + ".pulse_generator()",
                message="Pulse generator firmware option not enabled.",
            )
