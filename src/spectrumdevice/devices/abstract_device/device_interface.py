from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Tuple, TypeVar, Generic

from spectrumdevice.devices.abstract_device.channel_interfaces import (
    SpectrumAnalogChannelInterface,
    SpectrumIOLineInterface,
)
from spectrumdevice.settings import (
    AdvancedCardFeature,
    AvailableIOModes,
    CardFeature,
    ClockMode,
    DEVICE_STATUS_TYPE,
    ExternalTriggerMode,
    ModelNumber,
    SpectrumRegisterLength,
    TransferBuffer,
    TriggerSettings,
    TriggerSource,
)
from spectrumdevice.settings.card_dependent_properties import CardType
from spectrumdevice.settings.output_channel_pairing import ChannelPair, ChannelPairingMode

AnalogChannelInterfaceType = TypeVar("AnalogChannelInterfaceType", bound=SpectrumAnalogChannelInterface)
IOLineInterfaceType = TypeVar("IOLineInterfaceType", bound=SpectrumIOLineInterface)


class SpectrumDeviceInterface(Generic[AnalogChannelInterfaceType, IOLineInterfaceType], ABC):
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
    def analog_channels(self) -> Sequence[AnalogChannelInterfaceType]:
        raise NotImplementedError()

    @property
    def io_lines(self) -> Sequence[IOLineInterfaceType]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def enabled_analog_channel_nums(self) -> List[int]:
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
    def configure_channel_pairing(self, channel_pair: ChannelPair, mode: ChannelPairingMode) -> None:
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
