from abc import ABC
from threading import Lock
from typing import Dict

from numpy import float_, zeros
from numpy.typing import NDArray

from spectrum_gmbh.regs import (
    SPCM_FEAT_EXTFW_SEGSTAT,
    SPCM_FEAT_MULTI,
    SPCM_X0_AVAILMODES,
    SPCM_X1_AVAILMODES,
    SPCM_X2_AVAILMODES,
    SPCM_X3_AVAILMODES,
    SPCM_XMODE_DISABLE,
    SPC_MEMSIZE,
    SPC_PCIEXTFEATURES,
    SPC_PCIFEATURES,
    SPC_SEGMENTSIZE,
    SPC_TIMEOUT,
)
from spectrumdevice.devices.abstract_device.abstract_spectrum_device import AbstractSpectrumDevice
from spectrumdevice.exceptions import SpectrumDeviceNotConnected
from spectrumdevice.settings import SpectrumRegisterLength


class MockAbstractSpectrumDevice(AbstractSpectrumDevice, ABC):
    """Overrides methods of `AbstractSpectrumDevice` that communicate with hardware with mocked implementations, allowing
    software to be tested without Spectrum hardware connected or drivers installed, e.g. during CI. Instances of this
    class cannot be constructed directly - instantiate `MockAbstractSpectrumDigitiser` and `MockSpectrumStarHub` objects instead,
    which inherit from this class."""

    def __init__(self) -> None:
        self._param_dict: Dict[int, int] = {
            SPC_PCIFEATURES: SPCM_FEAT_MULTI,
            SPC_PCIEXTFEATURES: SPCM_FEAT_EXTFW_SEGSTAT,
            SPCM_X0_AVAILMODES: SPCM_XMODE_DISABLE,
            SPCM_X1_AVAILMODES: SPCM_XMODE_DISABLE,
            SPCM_X2_AVAILMODES: SPCM_XMODE_DISABLE,
            SPCM_X3_AVAILMODES: SPCM_XMODE_DISABLE,
            SPC_TIMEOUT: 1000,
            SPC_SEGMENTSIZE: 1000,
            SPC_MEMSIZE: 1000,
        }
        self._buffer_lock = Lock()
        self._enabled_channels = [0]
        self._on_device_buffer: NDArray[float_] = zeros(1000)
        self._previous_data = self._on_device_buffer.copy()

    def write_to_spectrum_device_register(
        self, spectrum_register: int, value: int, length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO
    ) -> None:
        """Simulates the setting of a parameter or command (register) on Spectrum hardware by storing its value
        internally.

        Args:
            spectrum_register (int): Mock Spectrum abstract_device register to set. Should be imported from regs.py, which is
                part of the spectrum_gmbh package written by Spectrum.
            value (int): Value to set the register to. Should be imported from regs.py, which is
                part of the spectrum_gmbh package written by Spectrum, or taken from one of the Enums provided by
                the settings package.
            length (`SpectrumRegisterLength`): Length in bits of the register being set. Either
                `SpectrumRegisterLength.THIRTY_TWO or `SpectrumRegisterLength.SIXTY_FOUR`. Check the Spectrum
                documentation for the register being set to determine the length to use. Default is 32 bit which is
                correct for the majority of cases.
        """
        if self.connected:
            self._param_dict[spectrum_register] = value
        else:
            raise SpectrumDeviceNotConnected("Mock abstract_device has been disconnected.")

    def read_spectrum_device_register(
        self, spectrum_register: int, length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO
    ) -> int:
        """Read the current value of a mock Spectrum register. Registers that are not set to the internal
         parameter store during __init__() will need to be set using set_spectrum_api_param() before they can be
        read.

        Args:
            spectrum_register (int): Mock spectrum abstract_device register to read. Should be imported from regs.py, which is
                part of the spectrum_gmbh package written by Spectrum, or taken from one of the Enums provided by
                the settings package.
            length (`SpectrumRegisterLength`): Length in bits of the register being read. Either
                `SpectrumRegisterLength.THIRTY_TWO` or `SpectrumRegisterLength.SIXTY_FOUR`. Check the Spectrum
                documentation for the register to determine the length to use. Default is 32 bit which is correct for
                the majority of cases.

        Returns:
            value (int): The value of the requested register.

        """
        if self.connected:
            if spectrum_register in self._param_dict:
                return self._param_dict[spectrum_register]
            else:
                self._param_dict[spectrum_register] = -1
                return -1
        else:
            raise SpectrumDeviceNotConnected("Mock abstract_device has been disconnected.")
