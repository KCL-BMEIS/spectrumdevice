from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from pyspecde.settings.card_features import CardFeature, AdvancedCardFeature
from pyspecde.settings.device_modes import AcquisitionMode, ClockMode
from pyspecde.settings.io_lines import IOLineMode, AvailableIOModes
from pyspecde.settings.transfer_buffer import TransferBuffer, CardToPCDataTransferBuffer
from pyspecde.settings.triggering import TriggerSource, ExternalTriggerMode
from pyspecde.settings.status import CARD_STATUS_TYPE, STAR_HUB_STATUS_TYPE, StatusCode


__all__ = [
    "AcquisitionSettings",
    "TriggerSettings",
    "AcquisitionMode",
    "ClockMode",
    "CardFeature",
    "AdvancedCardFeature",
    "IOLineMode",
    "AvailableIOModes",
    "TransferBuffer",
    "CardToPCDataTransferBuffer",
    "TriggerSource",
    "ExternalTriggerMode",
    "CARD_STATUS_TYPE",
    "STAR_HUB_STATUS_TYPE",
    "StatusCode",
    "SpectrumRegisterLength",
]


class SpectrumRegisterLength(Enum):
    """Enum defining the possible lengths of a spectrum register."""

    THIRTY_TWO = 0
    """32 bit register"""
    SIXTY_FOUR = 1
    """64 bit register"""

    def __repr__(self) -> str:
        return self.name


@dataclass
class TriggerSettings:
    trigger_sources: List[TriggerSource]
    external_trigger_mode: Optional[ExternalTriggerMode] = None
    external_trigger_level_in_mv: Optional[int] = None
    external_trigger_pulse_width_in_samples: Optional[int] = None


@dataclass
class AcquisitionSettings:
    acquisition_mode: AcquisitionMode
    sample_rate_in_hz: int
    acquisition_length_in_samples: int
    pre_trigger_length_in_samples: int
    timeout_in_ms: int
    enabled_channels: List[int]
    vertical_ranges_in_mv: List[int]
    vertical_offsets_in_percent: List[int]
