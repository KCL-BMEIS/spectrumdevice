"""Provides an Enum defining the possible modes of the IO lines of a Spectrum device, and a dataclass used to store
the modes supported by each channel of a device. Also provides a function for decoding the value received from a device
when queried about its supported IO line modes."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from dataclasses import dataclass
from enum import Enum
from typing import List

from spectrumdevice.spectrum_wrapper import decode_bitmap_using_list_of_ints
from spectrum_gmbh.regs import (
    SPCM_XMODE_DISABLE,
    SPCM_XMODE_ASYNCIN,
    SPCM_XMODE_ASYNCOUT,
    SPCM_XMODE_DIGIN,
    SPCM_XMODE_TRIGIN,
    SPCM_XMODE_DIGOUT,
    SPCM_XMODE_TRIGOUT,
    SPCM_XMODE_RUNSTATE,
    SPCM_XMODE_ARMSTATE,
    SPCM_XMODE_CONTOUTMARK,
)


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
