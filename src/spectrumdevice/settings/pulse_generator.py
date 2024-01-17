from dataclasses import dataclass
from enum import Enum

from spectrum_gmbh.py_header.regs import (
    SPCM_PULSEGEN_CONFIG_HIGH,
    SPCM_PULSEGEN_CONFIG_INVERT,
    SPCM_PULSEGEN_CONFIG_MUX1_INVERT,
    SPCM_PULSEGEN_CONFIG_MUX2_INVERT,
    SPCM_PULSEGEN_ENABLE0,
    SPCM_PULSEGEN_ENABLE1,
    SPCM_PULSEGEN_ENABLE2,
    SPCM_PULSEGEN_ENABLE3,
    SPCM_PULSEGEN_MODE_GATED,
    SPCM_PULSEGEN_MODE_SINGLESHOT,
    SPCM_PULSEGEN_MODE_TRIGGERED,
    SPCM_PULSEGEN_MUX1_SRC_ARM,
    SPCM_PULSEGEN_MUX1_SRC_RUN,
    SPCM_PULSEGEN_MUX1_SRC_UNUSED,
    SPCM_PULSEGEN_MUX2_SRC_PULSEGEN0,
    SPCM_PULSEGEN_MUX2_SRC_PULSEGEN1,
    SPCM_PULSEGEN_MUX2_SRC_PULSEGEN2,
    SPCM_PULSEGEN_MUX2_SRC_PULSEGEN3,
    SPCM_PULSEGEN_MUX2_SRC_SOFTWARE,
    SPCM_PULSEGEN_MUX2_SRC_UNUSED,
    SPCM_PULSEGEN_MUX2_SRC_XIO0,
    SPCM_PULSEGEN_MUX2_SRC_XIO1,
    SPCM_PULSEGEN_MUX2_SRC_XIO2,
    SPCM_PULSEGEN_MUX2_SRC_XIO3,
    SPC_XIO_PULSEGEN0_CONFIG,
    SPC_XIO_PULSEGEN0_HIGH,
    SPC_XIO_PULSEGEN0_LEN,
    SPC_XIO_PULSEGEN0_LOOPS,
    SPC_XIO_PULSEGEN0_MODE,
    SPC_XIO_PULSEGEN0_MUX1_SRC,
    SPC_XIO_PULSEGEN0_MUX2_SRC,
    SPC_XIO_PULSEGEN1_CONFIG,
    SPC_XIO_PULSEGEN1_HIGH,
    SPC_XIO_PULSEGEN1_LEN,
    SPC_XIO_PULSEGEN1_LOOPS,
    SPC_XIO_PULSEGEN1_MODE,
    SPC_XIO_PULSEGEN1_MUX1_SRC,
    SPC_XIO_PULSEGEN1_MUX2_SRC,
    SPC_XIO_PULSEGEN2_CONFIG,
    SPC_XIO_PULSEGEN2_HIGH,
    SPC_XIO_PULSEGEN2_LEN,
    SPC_XIO_PULSEGEN2_LOOPS,
    SPC_XIO_PULSEGEN2_MODE,
    SPC_XIO_PULSEGEN2_MUX1_SRC,
    SPC_XIO_PULSEGEN2_MUX2_SRC,
    SPC_XIO_PULSEGEN3_CONFIG,
    SPC_XIO_PULSEGEN3_HIGH,
    SPC_XIO_PULSEGEN3_LEN,
    SPC_XIO_PULSEGEN3_LOOPS,
    SPC_XIO_PULSEGEN3_MODE,
    SPC_XIO_PULSEGEN3_MUX1_SRC,
    SPC_XIO_PULSEGEN3_MUX2_SRC,
)
from spectrumdevice.spectrum_wrapper import decode_bitmap_using_list_of_ints

PULSE_GEN_ENABLE_COMMANDS = (SPCM_PULSEGEN_ENABLE0, SPCM_PULSEGEN_ENABLE1, SPCM_PULSEGEN_ENABLE2, SPCM_PULSEGEN_ENABLE3)


def decode_enabled_pulse_gens(value: int) -> list[int]:
    """Converts the integer value received by a Spectrum device when queried about its enabled pulse gens into a list of
    ids of the enable pulse generators."""
    possible_values = [v for v in PULSE_GEN_ENABLE_COMMANDS]
    return [found_value for found_value in decode_bitmap_using_list_of_ints(value, possible_values)]


class PulseGeneratorTriggerMode(Enum):
    SPCM_PULSEGEN_MODE_GATED = SPCM_PULSEGEN_MODE_GATED
    """Pulse generator will start if the trigger condition or “gate” is met and will stop, if either the gate becomes
    inactive or the defined number of LOOPS have been generated. Will reset its loop counter, when the gate becomes LOW.
    """
    SPCM_PULSEGEN_MODE_TRIGGERED = SPCM_PULSEGEN_MODE_TRIGGERED
    """The pulse generator will start if the trigger condition is met and will replay the defined number of loops
    before re-arm- ing itself and waiting for another trigger event. Changes in the trigger signal while replaying will
    be ignored."""
    SPCM_PULSEGEN_MODE_SINGLESHOT = SPCM_PULSEGEN_MODE_SINGLESHOT
    """The pulse generator will start if the trigger condition is met and will replay the defined number of loops once.
    """


PULSE_GEN_TRIGGER_MODE_COMMANDS = (
    SPC_XIO_PULSEGEN0_MODE,
    SPC_XIO_PULSEGEN1_MODE,
    SPC_XIO_PULSEGEN2_MODE,
    SPC_XIO_PULSEGEN3_MODE,
)


class PulseGeneratorMultiplexerTriggerSource:
    pass


class PulseGeneratorMultiplexer1TriggerSource(PulseGeneratorMultiplexerTriggerSource, Enum):
    SPCM_PULSEGEN_MUX1_SRC_UNUSED = SPCM_PULSEGEN_MUX1_SRC_UNUSED
    """Inputs of MUX1 are not used in creating the trigger condition and instead a static logic HIGH is used for MUX1.
    """
    SPCM_PULSEGEN_MUX1_SRC_RUN = SPCM_PULSEGEN_MUX1_SRC_RUN
    """This input of MUX1 reflects the current run state of the card. If acquisition/output is running the signal is
    HIGH. If card has stopped the signal is LOW. The signal is identical to XIO output using SPCM_XMODE_RUNSTATE."""
    SPCM_PULSEGEN_MUX1_SRC_ARM = SPCM_PULSEGEN_MUX1_SRC_ARM
    """This input of MUX1 reflects the current ARM state of the card. If the card is armed and ready to receive a
    trigger the signal is HIGH. If the card isn’t running or the card is still acquiring pretrigger data or the trigger
    has already been detected. the signal is LOW. The signal is identical to XIO output using SPCM_XMODE_ARMSTATE."""


PULSE_GEN_MUX1_COMMANDS = (
    SPC_XIO_PULSEGEN0_MUX1_SRC,
    SPC_XIO_PULSEGEN1_MUX1_SRC,
    SPC_XIO_PULSEGEN2_MUX1_SRC,
    SPC_XIO_PULSEGEN3_MUX1_SRC,
)


class PulseGeneratorMultiplexer2TriggerSource(PulseGeneratorMultiplexerTriggerSource, Enum):
    SPCM_PULSEGEN_MUX2_SRC_UNUSED = SPCM_PULSEGEN_MUX2_SRC_UNUSED
    SPCM_PULSEGEN_MUX2_SRC_SOFTWARE = SPCM_PULSEGEN_MUX2_SRC_SOFTWARE
    SPCM_PULSEGEN_MUX2_SRC_PULSEGEN0 = SPCM_PULSEGEN_MUX2_SRC_PULSEGEN0
    SPCM_PULSEGEN_MUX2_SRC_PULSEGEN1 = SPCM_PULSEGEN_MUX2_SRC_PULSEGEN1
    SPCM_PULSEGEN_MUX2_SRC_PULSEGEN2 = SPCM_PULSEGEN_MUX2_SRC_PULSEGEN2
    SPCM_PULSEGEN_MUX2_SRC_PULSEGEN3 = SPCM_PULSEGEN_MUX2_SRC_PULSEGEN3
    SPCM_PULSEGEN_MUX2_SRC_XIO0 = SPCM_PULSEGEN_MUX2_SRC_XIO0
    SPCM_PULSEGEN_MUX2_SRC_XIO1 = SPCM_PULSEGEN_MUX2_SRC_XIO1
    SPCM_PULSEGEN_MUX2_SRC_XIO2 = SPCM_PULSEGEN_MUX2_SRC_XIO2
    SPCM_PULSEGEN_MUX2_SRC_XIO3 = SPCM_PULSEGEN_MUX2_SRC_XIO3


PULSE_GEN_MUX2_COMMANDS = (
    SPC_XIO_PULSEGEN0_MUX2_SRC,
    SPC_XIO_PULSEGEN1_MUX2_SRC,
    SPC_XIO_PULSEGEN2_MUX2_SRC,
    SPC_XIO_PULSEGEN3_MUX2_SRC,
)


class PulseGeneratorTriggerDetectionMode(Enum):
    RISING_EDGE = 0  # this value is not defined in reg as really its just "HIGH" mode on or off
    SPCM_PULSEGEN_CONFIG_HIGH = SPCM_PULSEGEN_CONFIG_HIGH


@dataclass
class PulseGeneratorTriggerSettings:
    trigger_mode: PulseGeneratorTriggerMode
    trigger_detection_mode: PulseGeneratorTriggerDetectionMode
    multiplexer_1_source: PulseGeneratorMultiplexer1TriggerSource
    multiplexer_1_output_inversion: bool
    multiplexer_2_source: PulseGeneratorMultiplexer2TriggerSource
    multiplexer_2_output_inversion: bool


PULSE_GEN_CONFIG_COMMANDS = (
    SPC_XIO_PULSEGEN0_CONFIG,
    SPC_XIO_PULSEGEN1_CONFIG,
    SPC_XIO_PULSEGEN2_CONFIG,
    SPC_XIO_PULSEGEN3_CONFIG,
)


PULSE_GEN_MUX_INVERSION_COMMANDS = (SPCM_PULSEGEN_CONFIG_MUX1_INVERT, SPCM_PULSEGEN_CONFIG_MUX2_INVERT)


def decode_pulse_gen_config(value: int) -> list[int]:
    """Converts the integer value received by a Spectrum device when queried about its pulse gen configuration into a
    list of int16 values of the enabled configuration options."""
    possible_values = [
        SPCM_PULSEGEN_CONFIG_MUX1_INVERT,
        SPCM_PULSEGEN_CONFIG_MUX2_INVERT,
        SPCM_PULSEGEN_CONFIG_INVERT,
        int(PulseGeneratorTriggerDetectionMode.SPCM_PULSEGEN_CONFIG_HIGH.value),
    ]
    return [found_value for found_value in decode_bitmap_using_list_of_ints(value, possible_values)]


PULSE_GEN_PULSE_PERIOD_COMMANDS = (
    SPC_XIO_PULSEGEN0_LEN,
    SPC_XIO_PULSEGEN1_LEN,
    SPC_XIO_PULSEGEN2_LEN,
    SPC_XIO_PULSEGEN3_LEN,
)

PULSE_GEN_HIGH_DURATION_COMMANDS = (
    SPC_XIO_PULSEGEN0_HIGH,
    SPC_XIO_PULSEGEN1_HIGH,
    SPC_XIO_PULSEGEN2_HIGH,
    SPC_XIO_PULSEGEN3_HIGH,
)

PULSE_GEN_NUM_REPEATS_COMMANDS = (
    SPC_XIO_PULSEGEN0_LOOPS,
    SPC_XIO_PULSEGEN1_LOOPS,
    SPC_XIO_PULSEGEN2_LOOPS,
    SPC_XIO_PULSEGEN3_LOOPS,
)

PULSE_GEN_DELAY_COMMANDS = (
    601003,  # SPC_XIO_PULSEGEN0_DELAY not in regs.py for some reason
    601103,  # SPC_XIO_PULSEGEN1_DELAY not in regs.py for some reason
    601203,  # SPC_XIO_PULSEGEN2_DELAY not in regs.py for some reason
    601303,  # SPC_XIO_PULSEGEN3_DELAY not in regs.py for some reason
)


@dataclass
class PulseGeneratorOutputSettings:
    period_in_seconds: float
    duty_cycle: float
    num_pulses: int
    delay_in_seconds: float
    output_inversion: bool
