from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional

from numpy import ndarray

from pyspecde.sdk_translation_layer import (
    DEVICE_HANDLE_TYPE,
    TransferBuffer,
    AcquisitionMode,
    TriggerSource,
    ExternalTriggerMode,
    ClockMode,
    SpectrumChannelName,
)


class SpectrumChannelInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> SpectrumChannelName:
        raise NotImplementedError

    @property
    @abstractmethod
    def vertical_range_mv(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_vertical_range_mv(self, vertical_range: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def vertical_offset_percent(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_vertical_offset_percent(self, offset: int) -> None:
        raise NotImplementedError()


class SpectrumIntLengths(Enum):
    THIRTY_TWO = 0
    SIXTY_FOUR = 1


class SpectrumDeviceInterface(ABC):
    @property
    @abstractmethod
    def connected(self) -> bool:
        raise NotImplementedError()

    @property
    @abstractmethod
    def handle(self) -> DEVICE_HANDLE_TYPE:
        raise NotImplementedError()

    @abstractmethod
    def start_acquisition(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def stop_acquisition(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def wait_for_acquisition_to_complete(self) -> None:
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

    @abstractmethod
    def apply_channel_enabling(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def transfer_buffer(self) -> TransferBuffer:
        raise NotImplementedError()

    @abstractmethod
    def set_transfer_buffer(self, buffer: Optional[TransferBuffer] = None) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_waveforms(self) -> List[ndarray]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def channels(self) -> List[SpectrumChannelInterface]:
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
    def acquisition_length_samples(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_acquisition_length_samples(self, length_in_samples: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def post_trigger_length_samples(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_post_trigger_length_samples(self, length_in_samples: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def acquisition_mode(self) -> AcquisitionMode:
        raise NotImplementedError()

    @abstractmethod
    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def timeout_ms(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_timeout_ms(self, timeout_in_ms: int) -> None:
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
    def external_trigger_level_mv(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_external_trigger_level_mv(self, level: int) -> None:
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
    def sample_rate_hz(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_sample_rate_hz(self, rate: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def set_spectrum_api_param(
        self,
        spectrum_command: int,
        value: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_spectrum_api_param(
        self,
        spectrum_command: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> int:
        raise NotImplementedError()
