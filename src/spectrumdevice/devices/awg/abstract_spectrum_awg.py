from abc import ABC
from typing import Optional

from spectrum_gmbh.py_header.regs import M2CMD_CARD_WRITESETUP, SPC_CARDMODE, SPC_LOOPS, SPC_M2CMD
from spectrumdevice.devices.abstract_device import AbstractSpectrumDevice
from spectrumdevice.devices.awg.awg_interface import (
    SpectrumAWGAnalogChannelInterface,
    SpectrumAWGIOLineInterface,
    SpectrumAWGInterface,
)
from spectrumdevice.settings import GenerationSettings
from spectrumdevice.settings.device_modes import GenerationMode


class AbstractSpectrumAWG(
    AbstractSpectrumDevice[SpectrumAWGAnalogChannelInterface, SpectrumAWGIOLineInterface], SpectrumAWGInterface, ABC
):
    def configure_generation(self, generation_settings: GenerationSettings) -> None:
        """Apply all the settings contained in an `GenerationSettings` dataclass to the device.

        Args:
            generation_settings (`GenerationSettings`): A `GenerationSettings` dataclass containing the setting values
            to apply.
        """
        self.set_generation_mode(generation_settings.generation_mode)
        self.set_sample_rate_in_hz(generation_settings.sample_rate_in_hz)
        self.transfer_waveform(generation_settings.waveform)
        self.set_num_loops(generation_settings.num_loops)
        self.set_enabled_analog_channels(generation_settings.enabled_channels)
        if generation_settings.custom_stop_levels is None:
            custom_stop_levels: list[Optional[int]] = [None] * len(self.enabled_analog_channel_nums)
        else:
            custom_stop_levels = generation_settings.custom_stop_levels
        for channel_num, amp, dc, filt, stop_mode, stop_level in zip(
            self.enabled_analog_channel_nums,
            generation_settings.signal_amplitudes_in_mv,
            generation_settings.dc_offsets_in_mv,
            generation_settings.output_filters,
            generation_settings.stop_level_modes,
            custom_stop_levels,
        ):
            channel = self.analog_channels[channel_num]
            channel.set_signal_amplitude_in_mv(amp)
            channel.set_dc_offset_in_mv(dc)
            channel.set_output_filter(filt)
            channel.set_stop_level_mode(stop_mode)
            if stop_level is not None:
                channel.set_custom_stop_level(stop_level)
            channel.set_is_switched_on(True)

        # Write the configuration to the card
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_WRITESETUP)

    @property
    def generation_mode(self) -> GenerationMode:
        """Change the currently enabled card mode. See `GenerationMode` and the Spectrum documentation
        for the available modes."""
        return GenerationMode(self.read_spectrum_device_register(SPC_CARDMODE))

    def set_generation_mode(self, mode: GenerationMode) -> None:
        self.write_to_spectrum_device_register(SPC_CARDMODE, mode.value)

    @property
    def num_loops(self) -> int:
        return self.read_spectrum_device_register(SPC_LOOPS)

    def set_num_loops(self, num_loops: int) -> None:
        self.write_to_spectrum_device_register(SPC_LOOPS, num_loops)
