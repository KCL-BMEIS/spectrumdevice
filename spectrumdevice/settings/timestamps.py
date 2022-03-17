from datetime import datetime
from enum import Enum

from spectrum_gmbh.regs import (
    SPC_TSMODE_STANDARD,
    SPC_TSMODE_STARTRESET,
    SPC_TSCNT_REFCLOCKPOS,
    SPC_TSCNT_REFCLOCKNEG,
    SPC_TSCNT_INTERNAL,
    SPC_TSFEAT_NONE,
    SPC_TSMODE_DISABLE,
)


class TimestampMode(Enum):
    DISABLED = SPC_TSMODE_DISABLE
    """Timestamps are disabled"""
    STANDARD = SPC_TSMODE_STANDARD | SPC_TSCNT_INTERNAL | SPC_TSFEAT_NONE
    """Timestamps are provided relative to when the timestamp lock was manually reset."""
    STARTRESET = SPC_TSMODE_STARTRESET | SPC_TSCNT_INTERNAL | SPC_TSFEAT_NONE
    """Timestamps are provided relative to when the acquisition was started"""
    REFCLOCK_POS = SPC_TSMODE_STANDARD | SPC_TSCNT_REFCLOCKPOS | SPC_TSFEAT_NONE
    """Timestamps are provided relative to the rising edge of an external trigger signal"""
    REFCLOCK_NEG = SPC_TSMODE_STANDARD | SPC_TSCNT_REFCLOCKNEG | SPC_TSFEAT_NONE
    """Timestamps are provided relative to the falling edge of an external trigger signal"""


def spectrum_ref_time_to_datetime(ref_time_int: int, ref_date_int: int) -> datetime:

    hour = ref_time_int >> 16 & 0b1111111
    minute = ref_time_int >> 8 & 0b1111111
    second = ref_time_int >> 0 & 0b1111111
    year = ref_date_int >> 16 & 0b111111111111111
    month = ref_date_int >> 8 & 0b1111111
    day = ref_date_int >> 0 & 0b1111111

    return datetime(year, month, day, hour, minute, second)
