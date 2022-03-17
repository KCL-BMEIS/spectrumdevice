"""Provides Enums and Dataclasses wrapping the register values provided by the Spectrum API, to be used for configuring
hardware and interpreting responses received from hardware."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from spectrumdevice.settings.card_dependent_properties import CardType
from spectrumdevice.settings.card_features import CardFeature, AdvancedCardFeature
from spectrumdevice.settings.device_modes import AcquisitionMode, ClockMode
from spectrumdevice.settings.io_lines import IOLineMode, AvailableIOModes
from spectrumdevice.settings.transfer_buffer import TransferBuffer, CardToPCDataTransferBuffer
from spectrumdevice.settings.triggering import TriggerSource, ExternalTriggerMode
from spectrumdevice.settings.status import CARD_STATUS_TYPE, STAR_HUB_STATUS_TYPE, StatusCode


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
    "CardType",
]


@dataclass
class TriggerSettings:
    """A dataclass collecting all settings related to triggering. See Spectrum documentation."""

    trigger_sources: List[TriggerSource]
    """The trigger sources to enable"""
    external_trigger_mode: Optional[ExternalTriggerMode] = None
    """The external trigger mode (if an external trigger is enabled)."""
    external_trigger_level_in_mv: Optional[int] = None
    """The level an external signal must reach to cause a trigger event (if an external trigger is enabled)."""
    external_trigger_pulse_width_in_samples: Optional[int] = None
    """The required width of an external trigger pulse (if an external trigger is enabled)."""


@dataclass
class AcquisitionSettings:
    """A dataclass collecting all settings required to configure an acquisition. See Spectrum documentation."""

    acquisition_mode: AcquisitionMode
    """Standard Single mode or Multi FIF mode."""
    sample_rate_in_hz: int
    """Acquisition rate in samples per second."""
    acquisition_length_in_samples: int
    """The length of the recording in samples per channel."""
    pre_trigger_length_in_samples: int
    """The number of samples of the recording that will have been acquired before the trigger event."""
    timeout_in_ms: int
    """How long to wait for a trigger event before timing out."""
    enabled_channels: List[int]
    """The channel indices to enable for the acquisition."""
    vertical_ranges_in_mv: List[int]
    """The voltage range to apply to each enabled channel in mW."""
    vertical_offsets_in_percent: List[int]
    """The DC offset to apply to each enabled channel as percentages of their vertical ranges."""
    timestamping_enabled: bool
    """If True, Measurements will include the time at which the acquisition was triggered. Increases latency by ~10 ms.
    """


class SpectrumRegisterLength(Enum):
    """Enum defining the possible lengths of a spectrum register."""

    THIRTY_TWO = 0
    """32 bit register"""
    SIXTY_FOUR = 1
    """64 bit register"""

    def __repr__(self) -> str:
        return self.name
