from abc import ABC, abstractmethod

from numpy import int16
from numpy.typing import NDArray

from spectrumdevice.devices.abstract_device.device_interface import SpectrumDeviceInterface
from spectrumdevice.devices.abstract_device.channel_interfaces import (
    SpectrumAnalogChannelInterface,
    SpectrumIOLineInterface,
)
from spectrumdevice.settings import GenerationSettings
from spectrumdevice.settings.channel import OutputChannelFilter, OutputChannelStopLevelMode
from spectrumdevice.settings.device_modes import GenerationMode
from spectrumdevice.settings.io_lines import DigOutIOLineModeSettings


class SpectrumAWGIOLineInterface(SpectrumIOLineInterface, ABC):
    @property
    @abstractmethod
    def dig_out_settings(self) -> DigOutIOLineModeSettings:
        raise NotImplementedError()

    @abstractmethod
    def set_dig_out_settings(self, dig_out_settings: DigOutIOLineModeSettings) -> None:
        raise NotImplementedError()


class SpectrumAWGAnalogChannelInterface(SpectrumAnalogChannelInterface, ABC):
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
    def transfer_waveform(self, waveform: NDArray[int16]) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def num_loops(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_num_loops(self, num_loops: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def configure_generation(self, generation_settings: GenerationSettings) -> None:
        raise NotImplementedError()
