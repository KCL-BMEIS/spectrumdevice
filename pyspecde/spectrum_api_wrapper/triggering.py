from enum import Enum
from typing import List

from pyspecde.spectrum_api_wrapper import _decode_bitmap_using_enum
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
)


class TriggerSource(Enum):
    SPC_TMASK_SOFTWARE = SPC_TMASK_SOFTWARE
    SPC_TMASK_EXT0 = SPC_TMASK_EXT0
    SPC_TMASK_EXT1 = SPC_TMASK_EXT1
    SPC_TMASK_EXT2 = SPC_TMASK_EXT2
    SPC_TMASK_EXT3 = SPC_TMASK_EXT3
    SPC_TM_NONE = SPC_TM_NONE


class ExternalTriggerMode(Enum):
    SPC_TM_POS = SPC_TM_POS


def decode_trigger_sources(value: int) -> List[TriggerSource]:
    possible_values = [source.value for source in TriggerSource]
    return [TriggerSource(found_value) for found_value in _decode_bitmap_using_enum(value, possible_values)]


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
