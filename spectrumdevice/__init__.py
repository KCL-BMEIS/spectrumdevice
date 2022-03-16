"""
`spectrumdevice` is a high-level, object-oriented Python library for controlling Spectrum Instrumentation digitisers.

It can connect to individual digitisers or
[StarHubs](https://spectrum-instrumentation.com/en/m4i-star-hub) (e.g. the
[NetBox](https://spectrum-instrumentation.com/en/digitizernetbox)).

The main module `spectrumdevice` provides two classes `SpectrumCard` and `SpectrumStarHub` for controlling and receiving
data from individual digitisers and StarHubs respectively. Mock classes are also provided for testing software without
drivers installed or hardware connected.

The submodule `spectrumdevice.settings` provides Enums and Dataclasses wrapping the register values provided by the
Spectrum API, to be used for configuring hardware and interpreting responses received from hardware.

* [Source on GitHub](https://github.com/KCL-BMEIS/spectrumdevice)
* [README including quickstart](https://github.com/KCL-BMEIS/spectrumdevice/blob/main/README.md)
* [Examples](https://github.com/KCL-BMEIS/spectrumdevice/tree/main/example_scripts)
* [PyPi](https://pypi.org/project/spectrumdevice/)
* [API reference documentation](https://kcl-bmeis.github.io/spectrumdevice/)
"""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from .devices.measurement import Measurement
from .devices.spectrum_device import SpectrumDevice
from .devices.spectrum_card import SpectrumCard
from .devices.spectrum_channel import SpectrumChannel
from .devices.spectrum_star_hub import SpectrumStarHub
from spectrumdevice.devices.mocks import MockSpectrumCard, MockSpectrumStarHub

__all__ = [
    "SpectrumDevice",
    "SpectrumCard",
    "SpectrumStarHub",
    "SpectrumChannel",
    "MockSpectrumCard",
    "MockSpectrumStarHub",
    "settings",
    "Measurement",
]


from . import _version

__version__ = _version.get_versions()["version"]  # type: ignore
