"""Provides Enums and Dataclasses wrapping the register values provided by the Spectrum API, to be used for configuring
hardware and interpreting responses received from hardware."""

# Christian Baker, King's College London
# Copyright (c) 2024 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from .pulse_generator.pulse_generator import PulseGenerator

__all__ = ["PulseGenerator"]
