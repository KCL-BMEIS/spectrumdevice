"""Provides an Enum defining the possible modes of the IO lines of a Spectrum device, and a dataclass used to store
the modes supported by each channel of a device. Also provides a function for decoding the value received from a device
when queried about its supported IO line modes."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from dataclasses import dataclass
from enum import Enum
from typing import List

from spectrumdevice.settings.channel import SpectrumChannelName
from spectrumdevice.spectrum_wrapper import decode_bitmap_using_list_of_ints
from spectrum_gmbh.regs import (
    SPCM_XMODE_DISABLE,
    SPCM_XMODE_ASYNCIN,
    SPCM_XMODE_ASYNCOUT,
    SPCM_XMODE_DIGIN,
    SPCM_XMODE_PULSEGEN, SPCM_XMODE_TRIGIN,
    SPCM_XMODE_DIGOUT,
    SPCM_XMODE_TRIGOUT,
    SPCM_XMODE_RUNSTATE,
    SPCM_XMODE_ARMSTATE,
    SPCM_XMODE_CONTOUTMARK,
    SPCM_XMODE_DIGOUTSRC_CH0,
    SPCM_XMODE_DIGOUTSRC_CH6,
    SPCM_XMODE_DIGOUTSRC_CH5,
    SPCM_XMODE_DIGOUTSRC_CH4,
    SPCM_XMODE_DIGOUTSRC_CH3,
    SPCM_XMODE_DIGOUTSRC_CH2,
    SPCM_XMODE_DIGOUTSRC_CH1,
    SPCM_XMODE_DIGOUTSRC_CH7,
    SPCM_XMODE_DIGOUTSRC_BIT15,
    SPCM_XMODE_DIGOUTSRC_BIT14,
    SPCM_XMODE_DIGOUTSRC_BIT13,
    SPCM_XMODE_DIGOUTSRC_BIT12,
    SPCM_X0_MODE,
    SPCM_X1_MODE,
    SPCM_X15_MODE,
    SPCM_X14_MODE,
    SPCM_X13_MODE,
    SPCM_X12_MODE,
    SPCM_X11_MODE,
    SPCM_X10_MODE,
    SPCM_X9_MODE,
    SPCM_X8_MODE,
    SPCM_X7_MODE,
    SPCM_X6_MODE,
    SPCM_X5_MODE,
    SPCM_X4_MODE,
)


class SpectrumIOLineName(SpectrumChannelName):
    X0 = 0x00000001
    X1 = 0x00000002
    X2 = 0x00000004
    X3 = 0x00000008
    X4 = 0x00000010
    X5 = 0x00000020
    X6 = 0x00000040
    X7 = 0x00000080
    X8 = 0x00000100
    X9 = 0x00000200
    X10 = 0x00000400
    X11 = 0x00000800
    X12 = 0x00001000
    X13 = 0x00002000
    X14 = 0x00004000
    X15 = 0x00008000


class IOLineMode(Enum):
    """Enum representing the possible modes that a devices multi-purpose I/O line can support. A list of available
    modes for each I/O line on a device is provided by the devices available_io_modes property. See the Spectrum
    documentation for a description of each of the modes."""

    SPCM_XMODE_DISABLE = SPCM_XMODE_DISABLE
    SPCM_XMODE_ASYNCIN = SPCM_XMODE_ASYNCIN
    SPCM_XMODE_ASYNCOUT = SPCM_XMODE_ASYNCOUT
    SPCM_XMODE_DIGIN = SPCM_XMODE_DIGIN
    SPCM_XMODE_TRIGIN = SPCM_XMODE_TRIGIN
    SPCM_XMODE_DIGOUT = SPCM_XMODE_DIGOUT
    SPCM_XMODE_TRIGOUT = SPCM_XMODE_TRIGOUT
    SPCM_XMODE_RUNSTATE = SPCM_XMODE_RUNSTATE
    SPCM_XMODE_ARMSTATE = SPCM_XMODE_ARMSTATE
    SPCM_XMODE_CONTOUTMARK = SPCM_XMODE_CONTOUTMARK
    SPCM_XMODE_PULSEGEN = SPCM_XMODE_PULSEGEN


IO_LINE_MODE_COMMANDS = (
    SPCM_X0_MODE,
    SPCM_X1_MODE,
    SPCM_X4_MODE,
    SPCM_X5_MODE,
    SPCM_X6_MODE,
    SPCM_X7_MODE,
    SPCM_X8_MODE,
    SPCM_X9_MODE,
    SPCM_X10_MODE,
    SPCM_X11_MODE,
    SPCM_X12_MODE,
    SPCM_X13_MODE,
    SPCM_X14_MODE,
    SPCM_X15_MODE,
)


class DigOutSourceChannel(Enum):
    SPCM_XMODE_DIGOUTSRC_CH0 = SPCM_XMODE_DIGOUTSRC_CH0
    SPCM_XMODE_DIGOUTSRC_CH1 = SPCM_XMODE_DIGOUTSRC_CH1
    SPCM_XMODE_DIGOUTSRC_CH2 = SPCM_XMODE_DIGOUTSRC_CH2
    SPCM_XMODE_DIGOUTSRC_CH3 = SPCM_XMODE_DIGOUTSRC_CH3
    SPCM_XMODE_DIGOUTSRC_CH4 = SPCM_XMODE_DIGOUTSRC_CH4
    SPCM_XMODE_DIGOUTSRC_CH5 = SPCM_XMODE_DIGOUTSRC_CH5
    SPCM_XMODE_DIGOUTSRC_CH6 = SPCM_XMODE_DIGOUTSRC_CH6
    SPCM_XMODE_DIGOUTSRC_CH7 = SPCM_XMODE_DIGOUTSRC_CH7


class DigOutSourceBit(Enum):
    SPCM_XMODE_DIGOUTSRC_BIT15 = SPCM_XMODE_DIGOUTSRC_BIT15
    """Use Bit15 of selected channel: channel’s resolution will be reduced to 15 bit."""
    SPCM_XMODE_DIGOUTSRC_BIT14 = SPCM_XMODE_DIGOUTSRC_BIT14
    """Use Bit14 of selected channel: channel’s resolution will be reduced to 14 bit,
    even if bit 15 is not used for digital replay."""
    SPCM_XMODE_DIGOUTSRC_BIT13 = SPCM_XMODE_DIGOUTSRC_BIT13
    """Use Bit13 of selected channel: channel’s resolution will be reduced to 13 bit,
    even if bit 15 and/or bit 14 are not used for digital replay."""
    SPCM_XMODE_DIGOUTSRC_BIT12 = SPCM_XMODE_DIGOUTSRC_BIT12
    """Use Bit12 of selected channel: channel’s resolution will be reduced to 12 bit,
    even if bit 15 and/or bit 14 end/or bit 13 are not used for digital replay."""


@dataclass
class DigOutIOLineModeSettings:
    source_channel: DigOutSourceChannel
    source_bit: DigOutSourceBit


def decode_available_io_modes(value: int) -> List[IOLineMode]:
    """Converts the integer value received from a Spectrum device when queried about its IO line modes into a list
    of IOLineModes."""
    possible_values = [mode.value for mode in IOLineMode]
    return [IOLineMode(found_value) for found_value in decode_bitmap_using_list_of_ints(value, possible_values)]


@dataclass
class AvailableIOModes:
    """Stores a list of the available IOLineMode settings on each of the four I/O lines (X0, X1, X2 and X3) on a
    device. Returned by the available_io_modes() method of a device."""

    X0: List[IOLineMode]
    """IO modes available to the XO IO line."""
    X1: List[IOLineMode]
    """IO modes available to the X1 IO line."""
    X2: List[IOLineMode]
    """IO modes available to the X2 IO line."""
    X3: List[IOLineMode]
    """IO modes available to the X3 IO line."""
