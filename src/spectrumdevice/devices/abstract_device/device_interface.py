"""Defines a common public interface for controlling all Spectrum devices and their channels."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Tuple, Union

from spectrumdevice.settings import (
    AdvancedCardFeature,
    AvailableIOModes,
    CARD_STATUS_TYPE,
    CardFeature,
    CardToPCDataTransferBuffer,
    ClockMode,
    ExternalTriggerMode,
    STAR_HUB_STATUS_TYPE,
    SpectrumRegisterLength,
    TransferBuffer,
    TriggerSettings,
    TriggerSource,
)
from spectrumdevice.settings.channel import SpectrumChannelName


class SpectrumChannelInterface(ABC):
    """Defines the common public interface for control of the channels of Digitiser and AWG devices. All properties are
    read-only and must be set with their respective setter methods."""

    @property
    @abstractmethod
    def name(self) -> SpectrumChannelName:
        raise NotImplementedError


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
    def status(self) -> Union[CARD_STATUS_TYPE, STAR_HUB_STATUS_TYPE]:
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
    def wait_for_transfer_to_complete(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def transfer_buffers(self) -> List[TransferBuffer]:
        raise NotImplementedError()

    @abstractmethod
    def define_transfer_buffer(self, buffer: Optional[List[CardToPCDataTransferBuffer]] = None) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def channels(self) -> Sequence[SpectrumChannelInterface]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def enabled_channels(self) -> List[int]:
        raise NotImplementedError()

    @abstractmethod
    def set_enabled_channels(self, channels_nums: List[int]) -> None:
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
