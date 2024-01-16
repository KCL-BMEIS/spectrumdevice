"""Defines a common public interface for controlling all Spectrum devices and their channels."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Tuple, TypeVar, Generic

from spectrumdevice.features.pulse_generator.interfaces import PulseGeneratorInterface
from spectrumdevice.settings import (
    AdvancedCardFeature,
    AvailableIOModes,
    CardFeature,
    ClockMode,
    ExternalTriggerMode,
    DEVICE_STATUS_TYPE,
    ModelNumber,
    SpectrumRegisterLength,
    TransferBuffer,
    TriggerSettings,
    TriggerSource,
    IOLineMode,
)
from spectrumdevice.settings.card_dependent_properties import CardType
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


class SpectrumDeviceInterface(ABC):
    """Defines the common public interface for control of all digitiser and AWG devices, be they StarHub composite
    devices (e.g. the NetBox) or individual cards. All properties are read-only and must be set with their respective
    setter methods."""

    @property
    @abstractmethod
    def connected(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def reconnect(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError()

    @property
    def status(self) -> DEVICE_STATUS_TYPE:
        raise NotImplementedError()

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def start_transfer(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def stop_transfer(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def wait_for_transfer_chunk_to_complete(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def transfer_buffers(self) -> List[TransferBuffer]:
        raise NotImplementedError()

    @abstractmethod
    def define_transfer_buffer(self, buffer: Optional[Sequence[TransferBuffer]] = None) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def analog_channels(self) -> Sequence[SpectrumAnalogChannelInterface]:
        raise NotImplementedError()

    @property
    def io_lines(self) -> Sequence[SpectrumIOLineInterface]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def enabled_analog_channels(self) -> List[int]:
        raise NotImplementedError()

    @abstractmethod
    def set_enabled_analog_channels(self, channels_nums: List[int]) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def trigger_sources(self) -> List[TriggerSource]:
        raise NotImplementedError()

    @abstractmethod
    def set_trigger_sources(self, source: List[TriggerSource]) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def external_trigger_mode(self) -> ExternalTriggerMode:
        raise NotImplementedError()

    @abstractmethod
    def set_external_trigger_mode(self, mode: ExternalTriggerMode) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def external_trigger_level_in_mv(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_external_trigger_level_in_mv(self, level: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def external_trigger_pulse_width_in_samples(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_external_trigger_pulse_width_in_samples(self, width: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def configure_trigger(self, settings: TriggerSettings) -> None:
        raise NotImplementedError()

    @abstractmethod
    def apply_channel_enabling(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def clock_mode(self) -> ClockMode:
        raise NotImplementedError()

    @abstractmethod
    def set_clock_mode(self, mode: ClockMode) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def sample_rate_in_hz(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_sample_rate_in_hz(self, rate: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def available_io_modes(self) -> AvailableIOModes:
        raise NotImplementedError()

    @property
    @abstractmethod
    def feature_list(self) -> List[Tuple[List[CardFeature], List[AdvancedCardFeature]]]:
        raise NotImplementedError()

    @abstractmethod
    def write_to_spectrum_device_register(
        self,
        spectrum_register: int,
        value: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def read_spectrum_device_register(
        self,
        spectrum_register: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def timeout_in_ms(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_timeout_in_ms(self, timeout_in_ms: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def force_trigger_event(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def bytes_per_sample(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def type(self) -> CardType:
        raise NotImplementedError()

    @property
    @abstractmethod
    def model_number(self) -> ModelNumber:
        raise NotImplementedError()
