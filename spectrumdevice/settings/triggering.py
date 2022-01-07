"""Provides Enums defining the settings used to configure a trigger, and Dict lookup-tables for obtaining the Spectrum
API commands used to configure each external trigger input. Also provides a function for decoding the integer values
received by a device when queried about its enabled trigger sources."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from enum import Enum
from typing import List

from spectrumdevice.spectrum_wrapper import decode_bitmap_using_list_of_ints
from spectrum_gmbh.regs import (
    SPC_TMASK_SOFTWARE,
    SPC_TMASK_EXT0,
    SPC_TMASK_EXT1,
    SPC_TMASK_EXT2,
    SPC_TMASK_EXT3,
    SPC_TM_NONE,
    SPC_TM_POS,
    SPC_TRIG_EXT0_MODE,
    SPC_TRIG_EXT1_MODE,
    SPC_TRIG_EXT2_MODE,
    SPC_TRIG_EXT3_MODE,
    SPC_TRIG_EXT0_LEVEL0,
    SPC_TRIG_EXT1_LEVEL0,
    SPC_TRIG_EXT2_LEVEL0,
    SPC_TMASK_NONE,
    SPC_TM_NEG,
    SPC_TM_BOTH,
    SPC_TM_HIGH,
    SPC_TM_LOW,
    SPC_TM_PW_GREATER,
    SPC_TM_PW_SMALLER,
    SPC_TRIG_EXT0_PULSEWIDTH,
)


class TriggerSource(Enum):
    """An Enum representing the possible trigger sources."""

    SPC_TMASK_SOFTWARE = SPC_TMASK_SOFTWARE
    """Enables the software trigger for the OR mask. The card will trigger immediately after start."""
    SPC_TMASK_EXT0 = SPC_TMASK_EXT0
    """Enables the external (analog) trigger 0 for the OR mask."""
    SPC_TMASK_EXT1 = SPC_TMASK_EXT1
    """Enables the X1 (logic) trigger for the OR mask."""
    SPC_TMASK_EXT2 = SPC_TMASK_EXT2
    """Enables the X2 (logic) trigger for the OR mask."""
    SPC_TMASK_EXT3 = SPC_TMASK_EXT3
    """Enables the X3 (logic) trigger for the OR mask."""
    SPC_TMASK_NONE = SPC_TMASK_NONE
    """No trigger source selected."""


EXTERNAL_TRIGGER_SOURCES = [
    TriggerSource.SPC_TMASK_EXT0,
    TriggerSource.SPC_TMASK_EXT1,
    TriggerSource.SPC_TMASK_EXT2,
    TriggerSource.SPC_TMASK_EXT3,
]


class ExternalTriggerMode(Enum):
    """An Enum representing the supported trigger modes. See the Spectrum documentation more more Information.

    SPC_TM_NONE:
    SPC_TM_POS:
    SPC_TM_NEG:
    SPC_TM_BOTH:
    SPC_TM_HIGH:
    SPC_TM_LOW:
    SPC_TM_PW_GREATER:
    SPC_TM_PW_SMALLER:
    """

    SPC_TM_NONE = SPC_TM_NONE
    """Channel is not used for trigger detection."""
    SPC_TM_POS = SPC_TM_POS
    """Trigger detection for positive edges (crossing level 0 from below to above)."""
    SPC_TM_NEG = SPC_TM_NEG
    """Trigger detection for negative edges (crossing level 0 from above to below)."""
    SPC_TM_BOTH = SPC_TM_BOTH
    """Trigger detection for positive and negative edges (any crossing of level 0)."""
    SPC_TM_HIGH = SPC_TM_HIGH
    """Trigger detection for HIGH levels (signal above level 0)."""
    SPC_TM_LOW = SPC_TM_LOW
    """Trigger detection for LOW levels (signal below level 0)."""
    SPC_TM_PW_GREATER = SPC_TM_PW_GREATER
    """Sets the trigger mode for external trigger to detect pulses that are longer than the pulse width
    chosen using the devices set_external_trigger_pulse_width_in_samples() method. Can only be used in combination
    with one of the above modes."""
    SPC_TM_PW_SMALLER = SPC_TM_PW_SMALLER
    """Sets the trigger mode for external trigger to detect pulses that are shorter than the pulse width
    chosen using the devices set_external_trigger_pulse_width_in_samples() method. Can only be used in combination
    with one of the above modes."""


def decode_trigger_sources(value: int) -> List[TriggerSource]:
    """Converts the integer values provided by a device when queried about its enabled trigger source to a list of
    TriggerSources."""
    possible_values = [source.value for source in TriggerSource]
    return [TriggerSource(found_value) for found_value in decode_bitmap_using_list_of_ints(value, possible_values)]


EXTERNAL_TRIGGER_MODE_COMMANDS = {
    SPC_TMASK_EXT0: SPC_TRIG_EXT0_MODE,
    SPC_TMASK_EXT1: SPC_TRIG_EXT1_MODE,
    SPC_TMASK_EXT2: SPC_TRIG_EXT2_MODE,
    SPC_TMASK_EXT3: SPC_TRIG_EXT3_MODE,
}
EXTERNAL_TRIGGER_LEVEL_COMMANDS = {
    SPC_TMASK_EXT0: SPC_TRIG_EXT0_LEVEL0,
    SPC_TMASK_EXT1: SPC_TRIG_EXT1_LEVEL0,
    SPC_TMASK_EXT2: SPC_TRIG_EXT2_LEVEL0,
}
EXTERNAL_TRIGGER_PULSE_WIDTH_COMMANDS = {
    SPC_TMASK_EXT0: SPC_TRIG_EXT0_PULSEWIDTH,
    SPC_TMASK_EXT1: SPC_TRIG_EXT0_PULSEWIDTH,
    SPC_TMASK_EXT2: SPC_TRIG_EXT0_PULSEWIDTH,
}
