"""Provides an Enum defining the possible acquisition statuses of a Spectrum device, and Type variables annotating
the list of statuses returned by a card, and the list of lists of statuses returned by a StarHub. Also provides a
function for decoding the integer value received by a card when queried about its status."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from enum import Enum
from typing import List

from spectrumdevice.spectrum_wrapper import decode_bitmap_using_list_of_ints
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
    M2STAT_EXTRA_BLOCKREADY,
    M2STAT_EXTRA_END,
    M2STAT_EXTRA_OVERRUN,
    M2STAT_EXTRA_ERROR,
)


class StatusCode(Enum):
    """An Enum representing the possible status codes that can be returned by a SpectrumCard. See the Spectrum
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
    M2STAT_EXTRA_BLOCKREADY = M2STAT_EXTRA_BLOCKREADY
    M2STAT_EXTRA_END = M2STAT_EXTRA_END
    M2STAT_EXTRA_OVERRUN = M2STAT_EXTRA_OVERRUN
    M2STAT_EXTRA_ERROR = M2STAT_EXTRA_ERROR


CARD_STATUS_TYPE = List[StatusCode]
"""A list of StatusCodes that is returned when the status of an individual card is queried."""

STAR_HUB_STATUS_TYPE = List[CARD_STATUS_TYPE]
"""A list of CARD_STATUS_TYPE that is returned when the status of a StarHub is queried."""


def decode_status(code: int) -> CARD_STATUS_TYPE:
    """Converts the integer value received by a card when quereied about its status to a list of StatusCodes."""
    possible_codes = [code.value for code in StatusCode]
    return CARD_STATUS_TYPE(
        [StatusCode(found_code) for found_code in decode_bitmap_using_list_of_ints(code, possible_codes)]
    )
