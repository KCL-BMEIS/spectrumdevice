from enum import Enum
from typing import List

from pyspecde.spectrum_wrapper import _decode_bitmap_using_enum
from spectrum_gmbh.regs import (
    M2STAT_NONE,
    M2STAT_CARD_PRETRIGGER,
    M2STAT_CARD_TRIGGER,
    M2STAT_CARD_READY,
    M2STAT_CARD_SEGMENT_PRETRG,
    M2STAT_DATA_BLOCKREADY,
    M2STAT_DATA_END,
    M2STAT_DATA_OVERRUN,
    M2STAT_DATA_ERROR,
)


class StatusCode(Enum):
    """ An Enum representing the possible status codes that can be returned by a SpectrumCard. See the Spectrum
    documentation for a description of each status."""
    M2STAT_NONE = M2STAT_NONE
    M2STAT_CARD_PRETRIGGER = M2STAT_CARD_PRETRIGGER
    M2STAT_CARD_TRIGGER = M2STAT_CARD_TRIGGER
    M2STAT_CARD_READY = M2STAT_CARD_READY
    M2STAT_CARD_SEGMENT_PRETRG = M2STAT_CARD_SEGMENT_PRETRG
    M2STAT_DATA_BLOCKREADY = M2STAT_DATA_BLOCKREADY
    M2STAT_DATA_END = M2STAT_DATA_END
    M2STAT_DATA_OVERRUN = M2STAT_DATA_OVERRUN
    M2STAT_DATA_ERROR = M2STAT_DATA_ERROR
    M2STAT_EXTRA_BLOCKREADY = M2STAT_DATA_BLOCKREADY
    M2STAT_EXTRA_END = M2STAT_DATA_END
    M2STAT_EXTRA_OVERRUN = M2STAT_DATA_OVERRUN
    M2STAT_EXTRA_ERROR = M2STAT_DATA_ERROR


CARD_STATUS_TYPE = List[StatusCode]
"""A list of StatusCodes that is returned when the status of an individual card is queried."""

STAR_HUB_STATUS_TYPE = List[CARD_STATUS_TYPE]
"""A list of CARD_STATUS_TYPE that is returned when the status of a StarHub is queried."""


def decode_status(code: int) -> CARD_STATUS_TYPE:
    possible_codes = [code.value for code in StatusCode]
    return CARD_STATUS_TYPE([StatusCode(found_code) for found_code in _decode_bitmap_using_enum(code, possible_codes)])
