"""" Defines interfaces and partially implemented abstract classes containing code common to all Spectrum devices"""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from spectrumdevice.devices.abstract_device.abstract_spectrum_card import AbstractSpectrumCard
from spectrumdevice.devices.abstract_device.abstract_spectrum_channel import AbstractSpectrumChannel
from spectrumdevice.devices.abstract_device.abstract_spectrum_device import AbstractSpectrumDevice
from spectrumdevice.devices.abstract_device.abstract_spectrum_hub import AbstractSpectrumStarHub
from spectrumdevice.devices.abstract_device.device_interface import SpectrumChannelInterface, SpectrumDeviceInterface


__all__ = [
    "SpectrumChannelInterface",
    "AbstractSpectrumChannel",
    "SpectrumDeviceInterface",
    "AbstractSpectrumDevice",
    "AbstractSpectrumCard",
    "AbstractSpectrumStarHub",
]
