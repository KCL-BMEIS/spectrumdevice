from typing import List

from spectrum_gmbh.py_header.regs import SPCM_PULSEGEN_ENABLE0, SPCM_PULSEGEN_ENABLE1, SPCM_PULSEGEN_ENABLE2, \
    SPCM_PULSEGEN_ENABLE3, SPC_XIO_PULSEGEN0_HIGH, SPC_XIO_PULSEGEN0_LEN, SPC_XIO_PULSEGEN0_LOOPS, \
    SPC_XIO_PULSEGEN1_HIGH, SPC_XIO_PULSEGEN1_LEN, \
    SPC_XIO_PULSEGEN1_LOOPS, SPC_XIO_PULSEGEN2_HIGH, \
    SPC_XIO_PULSEGEN2_LEN, \
    SPC_XIO_PULSEGEN2_LOOPS, SPC_XIO_PULSEGEN3_HIGH, \
    SPC_XIO_PULSEGEN3_LEN, SPC_XIO_PULSEGEN3_LOOPS
from spectrumdevice.spectrum_wrapper import decode_bitmap_using_list_of_ints

PULSE_GEN_ENABLE_COMMANDS = (
    SPCM_PULSEGEN_ENABLE0,
    SPCM_PULSEGEN_ENABLE1,
    SPCM_PULSEGEN_ENABLE2,
    SPCM_PULSEGEN_ENABLE3
)


def decode_enabled_pulse_gens(value: int) -> list[int]:
    """Converts the integer value received by a Spectrum device when queried about its advanced features into a list of
    AdvancedCardFeatures."""
    possible_values = [v for v in PULSE_GEN_ENABLE_COMMANDS]
    return [
        found_value for found_value in decode_bitmap_using_list_of_ints(value, possible_values)
    ]


PULSE_GEN_PULSE_PERIOD_COMMANDS = (
    SPC_XIO_PULSEGEN0_LEN,
    SPC_XIO_PULSEGEN1_LEN,
    SPC_XIO_PULSEGEN2_LEN,
    SPC_XIO_PULSEGEN3_LEN
)

PULSE_GEN_HIGH_DURATION_COMMANDS = (
    SPC_XIO_PULSEGEN0_HIGH,
    SPC_XIO_PULSEGEN1_HIGH,
    SPC_XIO_PULSEGEN2_HIGH,
    SPC_XIO_PULSEGEN3_HIGH
)

PULSE_GEN_NUM_REPEATS_COMMANDS = (
    SPC_XIO_PULSEGEN0_LOOPS,
    SPC_XIO_PULSEGEN1_LOOPS,
    SPC_XIO_PULSEGEN2_LOOPS,
    SPC_XIO_PULSEGEN3_LOOPS
)

PULSE_GEN_DELAY_COMMANDS = (
    601003,  # SPC_XIO_PULSEGEN0_DELAY not in regs.py for some reason
    601103,  # SPC_XIO_PULSEGEN1_DELAY not in regs.py for some reason
    601203,  # SPC_XIO_PULSEGEN2_DELAY not in regs.py for some reason
    601303  # SPC_XIO_PULSEGEN3_DELAY not in regs.py for some reason
)
