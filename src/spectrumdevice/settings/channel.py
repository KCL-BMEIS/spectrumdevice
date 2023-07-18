"""Provides an Enum defining the possible channel names assigned by the Spectrum API, and List lookup-tables for
accessing the commands used to set vertical range and offset of each channel of a device."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from enum import Enum

from spectrum_gmbh.regs import (
    SPCM_STOPLVL_CUSTOM,
    SPCM_STOPLVL_HIGH,
    SPCM_STOPLVL_HOLDLAST,
    SPCM_STOPLVL_LOW,
    SPCM_STOPLVL_ZERO,
    SPC_AMP0,
    SPC_AMP1,
    SPC_AMP2,
    SPC_AMP3,
    SPC_AMP4,
    SPC_AMP5,
    SPC_AMP6,
    SPC_AMP7,
    SPC_AMP8,
    SPC_AMP9,
    SPC_AMP10,
    SPC_AMP11,
    SPC_AMP12,
    SPC_AMP13,
    SPC_AMP14,
    SPC_AMP15,
    SPC_CH0_CUSTOM_STOP,
    SPC_CH0_STOPLEVEL,
    SPC_CH1_CUSTOM_STOP,
    SPC_CH1_STOPLEVEL,
    SPC_CH2_CUSTOM_STOP,
    SPC_CH2_STOPLEVEL,
    SPC_CH3_CUSTOM_STOP,
    SPC_CH3_STOPLEVEL,
    SPC_CH4_CUSTOM_STOP,
    SPC_CH4_STOPLEVEL,
    SPC_CH5_CUSTOM_STOP,
    SPC_CH5_STOPLEVEL,
    SPC_CH6_CUSTOM_STOP,
    SPC_CH6_STOPLEVEL,
    SPC_CH7_CUSTOM_STOP,
    SPC_CH7_STOPLEVEL,
    SPC_ENABLEOUT0,
    SPC_ENABLEOUT1,
    SPC_ENABLEOUT2,
    SPC_ENABLEOUT3,
    SPC_ENABLEOUT4,
    SPC_ENABLEOUT5,
    SPC_ENABLEOUT6,
    SPC_ENABLEOUT7,
    SPC_FILTER0,
    SPC_FILTER1,
    SPC_FILTER2,
    SPC_FILTER3,
    SPC_FILTER4,
    SPC_FILTER5,
    SPC_FILTER6,
    SPC_FILTER7,
    SPC_OFFS0,
    SPC_OFFS1,
    SPC_OFFS2,
    SPC_OFFS3,
    SPC_OFFS4,
    SPC_OFFS5,
    SPC_OFFS6,
    SPC_OFFS7,
    SPC_OFFS8,
    SPC_OFFS9,
    SPC_OFFS10,
    SPC_OFFS11,
    SPC_OFFS12,
    SPC_OFFS13,
    SPC_OFFS14,
    SPC_OFFS15,
    CHANNEL0,
    CHANNEL1,
    CHANNEL2,
    CHANNEL3,
    CHANNEL4,
    CHANNEL5,
    CHANNEL6,
    CHANNEL7,
    CHANNEL8,
    CHANNEL9,
    CHANNEL10,
    CHANNEL11,
    CHANNEL12,
    CHANNEL13,
    CHANNEL14,
    CHANNEL15,
)

VERTICAL_RANGE_COMMANDS = (
    SPC_AMP0,
    SPC_AMP1,
    SPC_AMP2,
    SPC_AMP3,
    SPC_AMP4,
    SPC_AMP5,
    SPC_AMP6,
    SPC_AMP7,
    SPC_AMP8,
    SPC_AMP9,
    SPC_AMP10,
    SPC_AMP11,
    SPC_AMP12,
    SPC_AMP13,
    SPC_AMP14,
    SPC_AMP15,
)
VERTICAL_OFFSET_COMMANDS = (
    SPC_OFFS0,
    SPC_OFFS1,
    SPC_OFFS2,
    SPC_OFFS3,
    SPC_OFFS4,
    SPC_OFFS5,
    SPC_OFFS6,
    SPC_OFFS7,
    SPC_OFFS8,
    SPC_OFFS9,
    SPC_OFFS10,
    SPC_OFFS11,
    SPC_OFFS12,
    SPC_OFFS13,
    SPC_OFFS14,
    SPC_OFFS15,
)
OUTPUT_AMPLITUDE_COMMANDS = VERTICAL_RANGE_COMMANDS
OUTPUT_DC_OFFSET_COMMANDS = VERTICAL_OFFSET_COMMANDS

OUTPUT_CHANNEL_ON_OFF_COMMANDS = (
    SPC_ENABLEOUT0,
    SPC_ENABLEOUT1,
    SPC_ENABLEOUT2,
    SPC_ENABLEOUT3,
    SPC_ENABLEOUT4,
    SPC_ENABLEOUT5,
    SPC_ENABLEOUT6,
    SPC_ENABLEOUT7,
)

OUTPUT_FILTER_COMMANDS = (
    SPC_FILTER0,
    SPC_FILTER1,
    SPC_FILTER2,
    SPC_FILTER3,
    SPC_FILTER4,
    SPC_FILTER5,
    SPC_FILTER6,
    SPC_FILTER7,
)


class OutputChannelFilter(Enum):
    LOW_PASS_70_MHZ = 0
    LOW_PASS_20_MHZ = 1
    LOW_PASS_5_MHZ = 2
    LOW_PASS_1_MHZ = 3


OUTPUT_STOP_LEVEL_MODE_COMMANDS = (
    SPC_CH0_STOPLEVEL,
    SPC_CH1_STOPLEVEL,
    SPC_CH2_STOPLEVEL,
    SPC_CH3_STOPLEVEL,
    SPC_CH4_STOPLEVEL,
    SPC_CH5_STOPLEVEL,
    SPC_CH6_STOPLEVEL,
    SPC_CH7_STOPLEVEL,
)

OUTPUT_STOP_LEVEL_CUSTOM_VALUE_COMMANDS = (
    SPC_CH0_CUSTOM_STOP,
    SPC_CH1_CUSTOM_STOP,
    SPC_CH2_CUSTOM_STOP,
    SPC_CH3_CUSTOM_STOP,
    SPC_CH4_CUSTOM_STOP,
    SPC_CH5_CUSTOM_STOP,
    SPC_CH6_CUSTOM_STOP,
    SPC_CH7_CUSTOM_STOP,
)


class OutputChannelStopLevelMode(Enum):
    """Behavior of output channel when output is stopped or playback completes."""

    SPCM_STOPLVL_ZERO = SPCM_STOPLVL_ZERO
    """ Output level will go to zero."""
    SPCM_STOPLVL_LOW = SPCM_STOPLVL_LOW
    """ Output level will go to minimum possible negative value."""
    SPCM_STOPLVL_HIGH = SPCM_STOPLVL_HIGH
    """ Output level will go to maximum possible positive value."""
    SPCM_STOPLVL_HOLDLAST = SPCM_STOPLVL_HOLDLAST
    """ Output level will stay at the level of the last played sample."""
    SPCM_STOPLVL_CUSTOM = SPCM_STOPLVL_CUSTOM
    """ Output level will go to the value defined using AWGChannel.set_stop_level_custom_value()"""


class SpectrumChannelName(Enum):
    CHANNEL0 = CHANNEL0
    CHANNEL1 = CHANNEL1
    CHANNEL2 = CHANNEL2
    CHANNEL3 = CHANNEL3
    CHANNEL4 = CHANNEL4
    CHANNEL5 = CHANNEL5
    CHANNEL6 = CHANNEL6
    CHANNEL7 = CHANNEL7
    CHANNEL8 = CHANNEL8
    CHANNEL9 = CHANNEL9
    CHANNEL10 = CHANNEL10
    CHANNEL11 = CHANNEL11
    CHANNEL12 = CHANNEL12
    CHANNEL13 = CHANNEL13
    CHANNEL14 = CHANNEL14
    CHANNEL15 = CHANNEL15