from abc import ABC, abstractmethod

from numpy import int16

from spectrumdevice.devices.abstract_device import SpectrumChannelInterface, SpectrumDeviceInterface
from spectrumdevice.settings.channel import OutputChannelFilter, OutputChannelStopLevelMode
from spectrumdevice.settings.device_modes import GenerationMode
from spectrumdevice.settings.output_channel_pairing import ChannelPair, ChannelPairingMode


class SpectrumAWGChannelInterface(SpectrumChannelInterface, ABC):
    """Defines the public interface for control of the channels of Spectrum AWG device. All properties are read-
    only and must be set with their respective setter methods."""

    @property
    @abstractmethod
    def is_switched_on(self) -> bool:
        """SPC_ENABLEOUT0, SPC_ENABLEOUT01 etc"""
        raise NotImplementedError()

    @abstractmethod
    def set_is_switched_on(self, is_switched_on: bool) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def dc_offset_in_mv(self) -> int:
        """SPC_OFFS0"""
        raise NotImplementedError()

    @abstractmethod
    def set_dc_offset_in_mv(self, amplitude: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def signal_amplitude_in_mv(self) -> int:
        """SPC_AMP0"""
        raise NotImplementedError()

    @abstractmethod
    def set_signal_amplitude_in_mv(self, amplitude: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def output_filter(self) -> OutputChannelFilter:
        raise NotImplementedError()

    @abstractmethod
    def set_output_filter(self, filter: OutputChannelFilter) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def stop_level_mode(self) -> OutputChannelStopLevelMode:
        raise NotImplementedError()

    @abstractmethod
    def set_stop_level_mode(self, mode: OutputChannelStopLevelMode) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def stop_level_custom_value(self) -> int16:
        raise NotImplementedError()

    @abstractmethod
    def set_stop_level_custom_value(self, value: int16) -> None:
        raise NotImplementedError()


class SpectrumAWGInterface(SpectrumDeviceInterface, ABC):
    """Defines the public interface for control of all Spectrum AWG devices, be they StarHub composite devices
    (e.g. the NetBox) or individual AWG cards. All properties are read-only and must be set with their respective
    setter methods."""

    @property
    @abstractmethod
    def generation_mode(self) -> GenerationMode:
        raise NotImplementedError()

    @abstractmethod
    def set_generation_mode(self, mode: GenerationMode) -> None:
        raise NotImplementedError()

    @abstractmethod
    def configure_channel_pairing(self, channel_pair: ChannelPair, mode: ChannelPairingMode) -> None:
        raise NotImplementedError()
