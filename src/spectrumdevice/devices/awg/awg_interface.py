from abc import ABC, abstractmethod

from spectrumdevice.devices.abstract_device import SpectrumChannelInterface, SpectrumDeviceInterface
from spectrumdevice.settings.channel import OutputChannelFilter
from spectrumdevice.settings.output_channel_pairing import ChannelPair, ChannelPairingMode


class SpectrumAWGChannelInterface(SpectrumChannelInterface, ABC):
    """Defines the public interface for control of the channels of Spectrum AWG device. All properties are read-
    only and must be set with their respective setter methods."""

    @property
    @abstractmethod
    def is_switched_on(self) -> bool:
        """ SPC_ENABLEOUT0, SPC_ENABLEOUT01 etc """
        raise NotImplementedError()

    @abstractmethod
    def set_is_switched_on(self, is_switched_on: bool) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def dc_offset_in_mv(self) -> int:
        """ SPC_OFFS0 """
        raise NotImplementedError()

    @abstractmethod
    def set_dc_offset_in_mv(self, amplitude: int):
        raise NotImplementedError()

    @property
    @abstractmethod
    def signal_amplitude_in_mv(self) -> int:
        """ SPC_AMP0 """
        raise NotImplementedError()

    @abstractmethod
    def set_signal_amplitude_in_mv(self, amplitude: int):
        raise NotImplementedError()

    @property
    @abstractmethod
    def output_filter(self) -> OutputChannelFilter:
        raise NotImplementedError()

    @abstractmethod
    def set_output_filter(self, filter: OutputChannelFilter) -> None:
        raise NotImplementedError()


class SpectrumAWGInterface(SpectrumDeviceInterface, ABC):
    """Defines the public interface for control of all Spectrum AWG devices, be they StarHub composite devices
    (e.g. the NetBox) or individual AWG cards. All properties are read-only and must be set with their respective
    setter methods."""

    @abstractmethod
    def configure_channel_pairing(self, channel_pair: ChannelPair, mode: ChannelPairingMode):
        raise NotImplementedError()


