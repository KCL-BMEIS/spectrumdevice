"""Provides mock abstracts classes containing code common to all mock classes."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from abc import ABC
from threading import Event, Lock, Thread
from typing import Dict, Optional

from numpy import float_, ndarray, zeros
from numpy.typing import NDArray

from spectrum_gmbh.regs import (
    SPCM_FEAT_EXTFW_SEGSTAT,
    SPCM_FEAT_MULTI,
    SPCM_X0_AVAILMODES,
    SPCM_X1_AVAILMODES,
    SPCM_X2_AVAILMODES,
    SPCM_X3_AVAILMODES,
    SPCM_XMODE_DISABLE,
    SPC_CARDMODE,
    SPC_MEMSIZE,
    SPC_MIINST_MAXADCVALUE,
    SPC_PCIEXTFEATURES,
    SPC_PCIFEATURES,
    SPC_SEGMENTSIZE,
    SPC_TIMEOUT,
)
from spectrumdevice.devices.abstract_device import AbstractSpectrumDevice
from spectrumdevice.devices.digitiser.abstract_spectrum_digitiser import AbstractSpectrumDigitiser
from spectrumdevice.devices.mocks.mock_waveform_source import mock_waveform_source_factory
from spectrumdevice.exceptions import SpectrumDeviceNotConnected
from spectrumdevice.settings import AcquisitionMode, SpectrumRegisterLength


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
            spectrum_register (int): Mock Spectrum device register to set. Should be imported from regs.py, which is
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
            raise SpectrumDeviceNotConnected("Mock device has been disconnected.")

    def read_spectrum_device_register(
        self, spectrum_register: int, length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO
    ) -> int:
        """Read the current value of a mock Spectrum register. Registers that are not set to the internal
         parameter store during __init__() will need to be set using set_spectrum_api_param() before they can be
        read.

        Args:
            spectrum_register (int): Mock spectrum device register to read. Should be imported from regs.py, which is
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
            raise SpectrumDeviceNotConnected("Mock device has been disconnected.")


class MockAbstractSpectrumDigitiser(MockAbstractSpectrumDevice, AbstractSpectrumDigitiser, ABC):
    """Overrides methods of `AbstractSpectrumDigitiser` that communicate with hardware with mocked implementations, allowing
    software to be tested without Spectrum hardware connected or drivers installed, e.g. during CI. Instances of this
    class cannot be constructed directly - instantiate `MockAbstractSpectrumDigitiser` and `MockSpectrumStarHub` objects instead,
    which inherit from this class."""

    def __init__(self, source_frame_rate_hz: float = 10.0) -> None:
        """
        Args:
            source_frame_rate_hz (float): Frame rate at which a mock waveform source will generate waveforms.
        """
        MockAbstractSpectrumDevice.__init__(self)
        self._source_frame_rate_hz = source_frame_rate_hz
        self._param_dict[SPC_CARDMODE] = AcquisitionMode.SPC_REC_STD_SINGLE.value
        self._param_dict[SPC_MIINST_MAXADCVALUE] = 128

        self._buffer_lock = Lock()
        self._acquisition_stop_event = Event()
        self._acquisition_thread: Optional[Thread] = None
        self._timestamp_thread: Optional[Thread] = None
        self._enabled_channels = [0]
        self._on_device_buffer: ndarray = zeros(1000)
        self._previous_data = self._on_device_buffer.copy()

    def start(self) -> None:
        """Starts a mock waveform source in a separate thread. The source generates noise samples according to the
        number of currently enabled channels and the acquisition length, and places them in the virtual on device buffer
        (the _on_device_buffer attribute).
        """
        waveform_source = mock_waveform_source_factory(self.acquisition_mode)
        amplitude = self.read_spectrum_device_register(SPC_MIINST_MAXADCVALUE)
        self._acquisition_stop_event.clear()
        self._acquisition_thread = Thread(
            target=waveform_source,
            args=(
                self._acquisition_stop_event,
                self._source_frame_rate_hz,
                amplitude,
                self._on_device_buffer,
                self._buffer_lock,
            ),
        )
        self._acquisition_thread.start()

    def stop(self) -> None:
        """Stops the mock waveform source and timestamp threads."""
        self._acquisition_stop_event.set()
