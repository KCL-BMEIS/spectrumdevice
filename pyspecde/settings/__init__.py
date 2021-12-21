from enum import Enum

from pyspecde.settings.card_features import CardFeature, AdvancedCardFeature
from pyspecde.settings.device_modes import AcquisitionMode, ClockMode
from pyspecde.settings.io_lines import IOLineMode, AvailableIOModes
from pyspecde.settings.transfer_buffer import TransferBuffer, CardToPCDataTransferBuffer
from pyspecde.settings.triggering import TriggerSource, ExternalTriggerMode
from pyspecde.settings.status import CARD_STATUS_TYPE, STAR_HUB_STATUS_TYPE, StatusCode


__all__ = [
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
