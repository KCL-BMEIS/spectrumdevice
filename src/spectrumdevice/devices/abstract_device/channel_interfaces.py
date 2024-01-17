"""Defines a common public interface for controlling all Spectrum devices and their channels."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from spectrumdevice.features.pulse_generator.interfaces import PulseGeneratorInterface
from spectrumdevice.settings import (
    SpectrumRegisterLength,
    IOLineMode,
)
from spectrumdevice.settings.channel import SpectrumAnalogChannelName, SpectrumChannelName
from spectrumdevice.settings.io_lines import SpectrumIOLineName

ChannelNameType = TypeVar("ChannelNameType", bound=SpectrumChannelName)


class SpectrumChannelInterface(Generic[ChannelNameType], ABC):
    """Defines the common public interface for control of the channels of Digitiser and AWG devices including
    Multipurpose IO Lines. All properties are read-only and must be set with their respective setter methods."""

    @property
    @abstractmethod
    def name(self) -> ChannelNameType:
        raise NotImplementedError

    @abstractmethod
    def write_to_parent_device_register(
        self,
        spectrum_register: int,
        value: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def read_parent_device_register(
        self,
        spectrum_register: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> int:
        raise NotImplementedError()


class SpectrumAnalogChannelInterface(SpectrumChannelInterface[SpectrumAnalogChannelName], ABC):
    """Defines the common public interface for control of the analog channels of Digitiser and AWG devices. All
    properties are read-only and must be set with their respective setter methods."""

    pass


class SpectrumIOLineInterface(SpectrumChannelInterface[SpectrumIOLineName], ABC):
    """Defines the common public interface for control of the Multipurpose IO Lines of Digitiser and AWG devices. All
    properties are read-only and must be set with their respective setter methods."""

    @property
    @abstractmethod
    def mode(self) -> IOLineMode:
        """Returns the current mode of the IO Line."""
        raise NotImplementedError()

    @abstractmethod
    def set_mode(self, mode: IOLineMode) -> None:
        """Sets the current mode of the IO Line"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def pulse_generator(self) -> PulseGeneratorInterface:
        """Gets the IO line's pulse generator."""
        raise NotImplementedError()
