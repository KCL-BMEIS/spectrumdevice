"""
A high-level, object-oriented Python library for controlling Spectrum Instrumentation devices.

`spectrumdevice` can connect to individual cards or
[StarHubs](https://spectrum-instrumentation.com/en/m4i-star-hub) (e.g. the
[NetBox](https://spectrum-instrumentation.com/en/digitizernetbox)). `spectrumdevice` provides the following classes
for controlling devices:

### Hardware Classes
| Name                             | Purpose                                                 |
|----------------------------------|---------------------------------------------------------|
| `SpectrumDigitiserCard`          | Controlling individual digitiser cards                  |
| `SpectrumDigitiserStarHub`       | Controlling digitiser cards aggregated with a StarHub   |
| `SpectrumDigitiserAnalogChannel` | Controlling analog channels of a digitiser              |
| `SpectrumDigitiserIOLine`        | Controlling multipurpose IO lines of a digitiser        |
| `SpectrumAWGCard`                | Controlling individual AWG cards                        |
| `SpectrumAWGStarHub`             | (not yet implemented)                                   |
| `SpectrumAWGAnalogChannel`       | Controlling analog channels of an AWG                   |
| `SpectrumAWGIOLine`              | Controlling multipurpose IO lines of an AWG             |
| `PulseGenerator`                 | Controlling pulse generators belonging to IO lines      |

### Mock Classes
`spectrumdevice` also includes mock classes for testing software without drivers installed or hardware connected:

| Name                           | Purpose                                             |
|--------------------------------|-----------------------------------------------------|
| `MockSpectrumDigitiserCard`    | Mocking individual digitiser cards                  |
| `MockSpectrumDigitiserStarHub` | Mocking digitiser cards aggregated with a StarHub   |
| `MockSpectrumAWGCard`          | Mocking individual AWG cards                        |
| `MockSpectrumAWGStarHub`       | Mocking AWG cards aggregated with a StarHub         |

### Abstract Classes
The following abstract classes provide common implementations for methods whose functionality is identical across
different Spectrum devices. They cannot be instantiated themselves, but are included here as they contain
documentation for methods inherited by the concrete (and therefore instantiatable) classes above.

| Name                           | Purpose                                             |
|--------------------------------|-----------------------------------------------------|
| `AbstractSpectrumDevice`       | Implements methods common to all devices            |
| `AbstractSpectrumCard`         | Implements methods common to all card               |
| `AbstractSpectrumStarHub`      | Implements methods common to all hubs               |
| `AbstractSpectrumChannel`      | Implements methods common to all channels           |
| `AbstractSpectrumDigitiser`    | Implements methods common to all digitisers         |
| `AbstractSpectrumAWG`          | Implements methods common to all AWGs               |

### Settings
The submodule `spectrumdevice.settings` provides Enums and Dataclasses wrapping the register values provided by the
Spectrum API, to be used for configuring hardware and interpreting responses received from hardware.

### Resources
* [Source on GitHub](https://github.com/KCL-BMEIS/spectrumdevice)
* [README including quickstart](https://github.com/KCL-BMEIS/spectrumdevice/blob/main/README.md)
* [Examples](https://github.com/KCL-BMEIS/spectrumdevice/tree/main/example_scripts)
* [PyPi](https://pypi.org/project/spectrumdevice/)
* [API reference documentation](https://kcl-bmeis.github.io/spectrumdevice/)

### Reference Documentation
"""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from spectrumdevice.measurement import Measurement
from .devices.digitiser.digitiser_card import SpectrumDigitiserCard
from .devices.digitiser.digitiser_channel import SpectrumDigitiserAnalogChannel, SpectrumDigitiserIOLine
from .devices.digitiser.digitiser_star_hub import SpectrumDigitiserStarHub
from .devices.awg.awg_card import SpectrumAWGCard
from .devices.awg.awg_channel import SpectrumAWGAnalogChannel, SpectrumAWGIOLine
from .devices.mocks import MockSpectrumDigitiserCard, MockSpectrumDigitiserStarHub, MockSpectrumAWGCard
from .devices.abstract_device import (
    AbstractSpectrumDevice,
    AbstractSpectrumCard,
    AbstractSpectrumChannel,
    AbstractSpectrumStarHub,
)
from .devices.digitiser.abstract_spectrum_digitiser import AbstractSpectrumDigitiser
from .features.pulse_generator.pulse_generator import PulseGenerator

__all__ = [
    "SpectrumDigitiserAnalogChannel",
    "SpectrumDigitiserIOLine",
    "SpectrumDigitiserCard",
    "SpectrumDigitiserStarHub",
    "MockSpectrumDigitiserCard",
    "MockSpectrumDigitiserStarHub",
    "AbstractSpectrumDigitiser",
    "AbstractSpectrumStarHub",
    "AbstractSpectrumCard",
    "AbstractSpectrumDevice",
    "AbstractSpectrumChannel",
    "settings",
    "features",
    "Measurement",
    "SpectrumAWGCard",
    "MockSpectrumAWGCard",
    "SpectrumAWGAnalogChannel",
    "SpectrumAWGIOLine",
    "PulseGenerator",
]


from . import _version

__version__ = _version.get_versions()["version"]  # type: ignore
