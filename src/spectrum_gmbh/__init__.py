# Files in this module are provided free of charge by Spectrum GMBH with no restrictions on use.
# They have been included here to simplify installation of the spectrumdevice package.
import sys

from .py_header import regs, spcerr
sys.modules[__name__ + ".regs"] = regs
sys.modules[__name__ + ".spcerr"] = spcerr
