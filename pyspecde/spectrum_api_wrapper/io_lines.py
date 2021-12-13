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
    X0: List[IOLineMode]
    X1: List[IOLineMode]
    X2: List[IOLineMode]
    X3: List[IOLineMode]
