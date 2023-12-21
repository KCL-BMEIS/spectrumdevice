""" Provides classes for controlling Spectrum digitiser cards and hubs."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from spectrumdevice.devices.digitiser.digitiser_card import SpectrumDigitiserCard
from spectrumdevice.devices.digitiser.digitiser_channel import SpectrumDigitiserAnalogChannel
from spectrumdevice.devices.digitiser.digitiser_interface import (
    SpectrumDigitiserAnalogChannelInterface,
    SpectrumDigitiserInterface,
)
from spectrumdevice.devices.digitiser.digitiser_star_hub import SpectrumDigitiserStarHub

__all__ = [
    "SpectrumDigitiserAnalogChannelInterface",
    "SpectrumDigitiserAnalogChannel",
    "SpectrumDigitiserInterface",
    "SpectrumDigitiserCard",
    "SpectrumDigitiserStarHub",
]
