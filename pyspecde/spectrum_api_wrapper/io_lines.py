from dataclasses import dataclass
from enum import Enum
from typing import List

from pyspecde.spectrum_api_wrapper import _decode_bitmap_using_enum
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
    possible_values = [mode.value for mode in IOLineMode]
    return [IOLineMode(found_value) for found_value in _decode_bitmap_using_enum(value, possible_values)]


@dataclass
class AvailableIOModes:
    """Stores a list of the available IOLineMode settings on each of the four I/O lines (X0, X1, X2 and X3) on a
    device. Returned by the available_io_modes() method of a device."""

    X0: List[IOLineMode]
    X1: List[IOLineMode]
    X2: List[IOLineMode]
    X3: List[IOLineMode]
