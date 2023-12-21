from abc import ABC

from spectrumdevice import AbstractSpectrumChannel
from spectrumdevice.devices.abstract_device.interfaces import SpectrumIOLineInterface
from spectrumdevice.settings import IOLineMode


class AbstractSpectrumIOLine(SpectrumIOLineInterface, AbstractSpectrumChannel, ABC):
    """Partially implemented abstract superclass contain code common for controlling an individual IO Line of all
    spectrum devices."""

    @property
    def _name_prefix(self) -> str:
        return "X"

    @property
    def mode(self) -> IOLineMode:
        """Returns the current mode of the IO Line."""
        raise NotImplementedError()

    def set_mode(self, mode: IOLineMode) -> None:
        """Sets the current mode of the IO Line"""
        raise NotImplementedError()
