"""Provides Enums defining the possible acquisition and clock modes of a spectrum device."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from enum import Enum

from spectrum_gmbh.regs import (
    SPC_REC_STD_SINGLE,
    SPC_REC_FIFO_MULTI,
    SPC_CM_INTPLL,
    SPC_CM_EXTERNAL,
    SPC_CM_EXTREFCLOCK,
)


class AcquisitionMode(Enum):
    """Enum representing the acquisition modes currently support by spectrumdevice. See Spectrum documentation for more
    information about each mode."""

    SPC_REC_STD_SINGLE = SPC_REC_STD_SINGLE
    """Data acquisition to on-board memory for one single trigger event."""
    SPC_REC_FIFO_MULTI = SPC_REC_FIFO_MULTI
    """Continuous data acquisition for multiple trigger events."""


class ClockMode(Enum):
    """Enum representing the clock modes currently supported by spectrumdevice. See Spectrum documentation for more
    information about each mode."""

    SPC_CM_INTPLL = SPC_CM_INTPLL
    """Enables internal PLL with 20 MHz internal reference for sample clock generation."""
    SPC_CM_EXTERNAL = SPC_CM_EXTERNAL
    """Enables external clock input for direct sample clock generation."""
    SPC_CM_EXTREFCLOCK = SPC_CM_EXTREFCLOCK
    """Enables internal PLL with external reference for sample clock generation."""
