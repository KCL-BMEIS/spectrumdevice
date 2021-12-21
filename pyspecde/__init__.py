"""
.. include:: ../README.md
"""
from .devices.spectrum_device import SpectrumDevice
from .devices.spectrum_card import SpectrumCard
from .devices.spectrum_channel import SpectrumChannel
from .devices.spectrum_star_hub import SpectrumStarHub
from .devices.mock_devices import MockSpectrumCard
from .devices.mock_devices import MockSpectrumStarHub

__docformat__ = "restructuredtext"

__all__ = [
    "SpectrumDevice",
    "SpectrumCard",
    "SpectrumStarHub",
    "SpectrumChannel",
    "MockSpectrumCard",
    "MockSpectrumStarHub",
    "settings",
]
