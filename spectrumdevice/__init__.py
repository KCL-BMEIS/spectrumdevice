"""
`spectrumdevice` is a high-level, object-oriented Python API for controlling Spectrum Instruments digitisers.

It can connect to individual digitisers or
[StarHubs](https://spectrum-instrumentation.com/en/m4i-star-hub) (e.g. the
[NetBox](https://spectrum-instrumentation.com/en/digitizernetbox)). `spectrumdevice` provides two classes
`SpectrumCard` and `SpectrumStarHub` for controlling and receiving data from individual digitisers and StarHubs
respectively.

For quickstart information, please see the [README](https://github.com/KCL-BMEIS/spectrumdevice/blob/main/README.md).

Examples can be found in the `example_scripts` module of the repository.
"""

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
