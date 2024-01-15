from typing import Any, cast

from numpy import int16

from spectrumdevice.devices.abstract_device import AbstractSpectrumCard
from spectrumdevice.devices.abstract_device.abstract_spectrum_channel import AbstractSpectrumAnalogChannel
from spectrumdevice.devices.abstract_device.abstract_spectrum_io_line import AbstractSpectrumIOLine
from spectrumdevice.devices.awg.awg_interface import (
    SpectrumAWGAnalogChannelInterface,
    SpectrumAWGIOLineInterface,
    SpectrumAWGInterface,
)
from spectrumdevice.exceptions import SpectrumCardIsNotAnAWG
from spectrumdevice.settings import IOLineMode
from spectrumdevice.settings.card_dependent_properties import CardType, OUTPUT_AMPLITUDE_LIMITS_IN_MV
from spectrumdevice.settings.channel import (
    OUTPUT_AMPLITUDE_COMMANDS,
    OUTPUT_CHANNEL_ON_OFF_COMMANDS,
    OUTPUT_DC_OFFSET_COMMANDS,
    OUTPUT_FILTER_COMMANDS,
    OUTPUT_STOP_LEVEL_CUSTOM_VALUE_COMMANDS,
    OUTPUT_STOP_LEVEL_MODE_COMMANDS,
    OutputChannelFilter,
    OutputChannelStopLevelMode,
)
from spectrumdevice.settings.io_lines import (
    DigOutIOLineModeSettings,
    DigOutSourceChannel,
    DigOutSourceBit,
)


class SpectrumAWGIOLine(AbstractSpectrumIOLine, SpectrumAWGIOLineInterface):
    def __init__(self, parent_device: AbstractSpectrumCard, **kwargs: Any) -> None:
        if parent_device.type != CardType.SPCM_TYPE_AO:
            raise SpectrumCardIsNotAnAWG(parent_device.type)
        super().__init__(parent_device=parent_device, **kwargs)  # pass unused args up the inheritance hierarchy
        self._dig_out_settings = DigOutIOLineModeSettings(
            source_channel=DigOutSourceChannel.SPCM_XMODE_DIGOUTSRC_CH0,
            source_bit=DigOutSourceBit.SPCM_XMODE_DIGOUTSRC_BIT15,
        )

    @property
    def dig_out_settings(self) -> DigOutIOLineModeSettings:
        return self._dig_out_settings

    def set_dig_out_settings(self, dig_out_settings: DigOutIOLineModeSettings) -> None:
        self._dig_out_settings = dig_out_settings

    def _get_io_line_mode_settings_mask(self, mode: IOLineMode) -> int:
        if mode == IOLineMode.SPCM_XMODE_DIGOUT:
            return cast(int, self._dig_out_settings.source_channel.value | self._dig_out_settings.source_bit.value)
        else:
            return 0


class SpectrumAWGAnalogChannel(AbstractSpectrumAnalogChannel, SpectrumAWGAnalogChannelInterface):
    def __init__(self, parent_device: SpectrumAWGInterface, **kwargs: Any) -> None:
        if parent_device.type != CardType.SPCM_TYPE_AO:
            raise SpectrumCardIsNotAnAWG(parent_device.type)
        super().__init__(parent_device=parent_device, **kwargs)  # pass unused args up the inheritance hierarchy

    @property
    def is_switched_on(self) -> bool:
        """Returns "True" if the output channel is switched on, or "False" if it is muted."""
        return bool(self._parent_device.read_spectrum_device_register(OUTPUT_CHANNEL_ON_OFF_COMMANDS[self._number]))

    def set_is_switched_on(self, is_switched_on: bool) -> None:
        """Switches the output channel on ("True") or off ("False")."""
        self._parent_device.write_to_spectrum_device_register(
            OUTPUT_CHANNEL_ON_OFF_COMMANDS[self._number], int(is_switched_on)
        )

    @property
    def dc_offset_in_mv(self) -> int:
        """The current output signal DC offset in mV.

        Returns:
            dc_offset (int): The currently set output signal DC offset in mV.
        """
        return self._parent_device.read_spectrum_device_register(OUTPUT_DC_OFFSET_COMMANDS[self._number])

    def set_dc_offset_in_mv(self, dc_offset: int) -> None:
        if dc_offset > OUTPUT_AMPLITUDE_LIMITS_IN_MV[self._parent_device.model_number]:
            raise ValueError(
                f"Max allowed signal DC offset for card {self._parent_device.model_number} is "
                f"{OUTPUT_AMPLITUDE_LIMITS_IN_MV[self._parent_device.model_number]} mV, "
                f"so {dc_offset} mV is too high."
            )
        self._parent_device.write_to_spectrum_device_register(OUTPUT_DC_OFFSET_COMMANDS[self._number], dc_offset)

    @property
    def signal_amplitude_in_mv(self) -> int:
        """The current output signal amplitude in mV.

        Returns:
            amplitude (int): The currently set output signal amplitude in mV.
        """
        return self._parent_device.read_spectrum_device_register(OUTPUT_AMPLITUDE_COMMANDS[self._number])

    def set_signal_amplitude_in_mv(self, amplitude: int) -> None:
        if amplitude > OUTPUT_AMPLITUDE_LIMITS_IN_MV[self._parent_device.model_number]:
            raise ValueError(
                f"Max allowed signal amplitude for card {self._parent_device.model_number} is "
                f"{OUTPUT_AMPLITUDE_LIMITS_IN_MV[self._parent_device.model_number]} mV, "
                f"so {amplitude} mV is too high."
            )
        self._parent_device.write_to_spectrum_device_register(OUTPUT_AMPLITUDE_COMMANDS[self._number], amplitude)

    @property
    def output_filter(self) -> OutputChannelFilter:
        """The current output filter setting.

        Returns:
            output_filter (OutputChannelFilter): The currently set output filter.
        """
        return OutputChannelFilter(
            self._parent_device.read_spectrum_device_register(OUTPUT_FILTER_COMMANDS[self._number])
        )

    def set_output_filter(self, output_filter: OutputChannelFilter) -> None:
        self._parent_device.write_to_spectrum_device_register(OUTPUT_FILTER_COMMANDS[self._number], output_filter.value)

    @property
    def stop_level_mode(self) -> OutputChannelStopLevelMode:
        """Sets the behavior of the channel when the output is stopped or playback finished."""
        return OutputChannelStopLevelMode(
            self._parent_device.read_spectrum_device_register(OUTPUT_STOP_LEVEL_MODE_COMMANDS[self._number])
        )

    def set_stop_level_mode(self, mode: OutputChannelStopLevelMode) -> None:
        self._parent_device.write_to_spectrum_device_register(OUTPUT_STOP_LEVEL_MODE_COMMANDS[self._number], mode.value)

    @property
    def stop_level_custom_value(self) -> int16:
        """Sets the level to which the output will be set when the output is stopped or playback finished and
        stop_level_mode is set to `OutputChannelStopLevelMode.SPCM_STOPLVL_CUSTOM`."""
        return int16(
            self._parent_device.read_spectrum_device_register(OUTPUT_STOP_LEVEL_CUSTOM_VALUE_COMMANDS[self._number])
        )

    def set_stop_level_custom_value(self, value: int16) -> None:
        self._parent_device.write_to_spectrum_device_register(
            OUTPUT_STOP_LEVEL_CUSTOM_VALUE_COMMANDS[self._number], int(value)
        )
