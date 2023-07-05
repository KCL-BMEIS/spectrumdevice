from abc import ABC
from copy import copy
from typing import cast

from spectrum_gmbh.regs import SPC_CARDMODE
from spectrumdevice import AbstractSpectrumDevice
from spectrumdevice.devices.awg.awg_channel import AWGChannel
from spectrumdevice.devices.awg.awg_interface import SpectrumAWGInterface
from spectrumdevice.settings.device_modes import GenerationMode
from spectrumdevice.settings.output_channel_pairing import (
    ChannelPair,
    ChannelPairingMode,
    DIFFERENTIAL_CHANNEL_PAIR_COMMANDS,
    DOUBLING_CHANNEL_PAIR_COMMANDS,
)


class AbstractSpectrumAWG(SpectrumAWGInterface, AbstractSpectrumDevice, ABC):
    @property
    def generation_mode(self) -> GenerationMode:
        """Change the currently enabled card mode. See `GenerationMode` and the Spectrum documentation
        for the available modes."""
        return GenerationMode(self.read_spectrum_device_register(SPC_CARDMODE))

    def set_generation_mode(self, mode: GenerationMode) -> None:
        self.write_to_spectrum_device_register(SPC_CARDMODE, mode.value)

    def configure_channel_pairing(self, channel_pair: ChannelPair, mode: ChannelPairingMode) -> None:
        """Configures a pair of consecutive channels to operate either independentally, in differential mode or
        in double  mode. If enabling differential or double mode, then the odd-numbered channel will be automatically
        configured to be identical to the even-numbered channel, and the odd-numbered channel will be disabled as is
        required by the Spectrum API.

        Args:
            channel_pair (ChannelPair): The pair of channels to configure
            mode (ChannelPairingMode): The mode to enable: SINGLE, DOUBLE, or DIFFERENTIAL
        """

        doubling_enabled = int(mode == ChannelPairingMode.DOUBLE)
        differential_mode_enabled = int(mode == ChannelPairingMode.DIFFERENTIAL)

        if doubling_enabled and channel_pair in (channel_pair.CHANNEL_4_AND_5, channel_pair.CHANNEL_6_AND_7):
            raise ValueError("Doubling can only be enabled for channel pairs CHANNEL_0_AND_1 or CHANNEL_2_AND_3.")

        if doubling_enabled or differential_mode_enabled:
            self._mirror_even_channel_settings_on_odd_channel(channel_pair)
            self._disable_odd_channel(channel_pair)

        self.write_to_spectrum_device_register(
            DIFFERENTIAL_CHANNEL_PAIR_COMMANDS[channel_pair], differential_mode_enabled
        )
        self.write_to_spectrum_device_register(DOUBLING_CHANNEL_PAIR_COMMANDS[channel_pair], doubling_enabled)

    def _disable_odd_channel(self, channel_pair: ChannelPair) -> None:
        try:
            enabled_channels = copy(self.enabled_channels)
            enabled_channels.remove(channel_pair.value + 1)
            self.set_enabled_channels(enabled_channels)
        except ValueError:
            pass  # odd numbered channel was not enable, so no need to disable it.

    def _mirror_even_channel_settings_on_odd_channel(self, channel_pair: ChannelPair) -> None:
        cast(AWGChannel, self.channels[channel_pair.value + 1]).set_signal_amplitude_in_mv(
            cast(AWGChannel, self.channels[channel_pair.value]).signal_amplitude_in_mv
        )
        cast(AWGChannel, self.channels[channel_pair.value + 1]).set_dc_offset_in_mv(
            cast(AWGChannel, self.channels[channel_pair.value]).dc_offset_in_mv
        )
        cast(AWGChannel, self.channels[channel_pair.value + 1]).set_output_filter(
            cast(AWGChannel, self.channels[channel_pair.value]).output_filter
        )
