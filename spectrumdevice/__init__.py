"""
.. include:: ../README.md
"""
__docformat__ = "restructuredtext"

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from .devices.spectrum_device import SpectrumDevice
from .devices.spectrum_card import SpectrumCard
from .devices.spectrum_channel import SpectrumChannel
from .devices.spectrum_star_hub import SpectrumStarHub
from .devices.mock_devices import MockSpectrumCard
from .devices.mock_devices import MockSpectrumStarHub

__all__ = [
    "SpectrumDevice",
    "SpectrumCard",
    "SpectrumStarHub",
    "SpectrumChannel",
    "MockSpectrumCard",
    "MockSpectrumStarHub",
    "settings",
]
