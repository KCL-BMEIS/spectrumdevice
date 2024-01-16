"""Provides mock abstracts classes containing code common to all mock classes."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from abc import ABC
from functools import reduce
from operator import or_
from threading import Event, Lock, Thread
from typing import Any, Dict, Optional, Union, cast

from spectrum_gmbh.regs import (
    SPCM_X0_AVAILMODES,
    SPCM_X1_AVAILMODES,
    SPCM_X2_AVAILMODES,
    SPCM_X3_AVAILMODES,
    SPCM_XMODE_DISABLE,
    SPC_CARDMODE,
    SPC_FNCTYPE,
    SPC_MEMSIZE,
    SPC_MIINST_BYTESPERSAMPLE,
    SPC_MIINST_MAXADCVALUE,
    SPC_PCIEXTFEATURES,
    SPC_PCIFEATURES,
    SPC_PCITYP,
    SPC_SEGMENTSIZE,
    SPC_TIMEOUT,
    SPC_MIINST_MODULES,
    SPC_MIINST_CHPERMODULE,
)

from spectrum_gmbh.py_header.regs import (
    SPCM_PULSEGEN_MODE_GATED,
    SPC_AMP0,
    SPC_AMP1,
    SPC_AMP10,
    SPC_AMP11,
    SPC_AMP12,
    SPC_AMP13,
    SPC_AMP14,
    SPC_AMP15,
    SPC_AMP2,
    SPC_AMP3,
    SPC_AMP4,
    SPC_AMP5,
    SPC_AMP6,
    SPC_AMP7,
    SPC_AMP8,
    SPC_AMP9,
    SPC_OFFS0,
    SPC_OFFS1,
    SPC_OFFS10,
    SPC_OFFS11,
    SPC_OFFS12,
    SPC_OFFS13,
    SPC_OFFS14,
    SPC_OFFS15,
    SPC_OFFS2,
    SPC_OFFS3,
    SPC_OFFS4,
    SPC_OFFS5,
    SPC_OFFS6,
    SPC_OFFS7,
    SPC_OFFS8,
    SPC_OFFS9,
    SPC_XIO_PULSEGEN0_CONFIG,
    SPC_XIO_PULSEGEN0_HIGH,
    SPC_XIO_PULSEGEN0_LEN,
    SPC_XIO_PULSEGEN0_LOOPS,
    SPC_XIO_PULSEGEN0_MODE,
    SPC_XIO_PULSEGEN1_CONFIG,
    SPC_XIO_PULSEGEN1_HIGH,
    SPC_XIO_PULSEGEN1_LEN,
    SPC_XIO_PULSEGEN1_LOOPS,
    SPC_XIO_PULSEGEN1_MODE,
    SPC_XIO_PULSEGEN2_CONFIG,
    SPC_XIO_PULSEGEN2_HIGH,
    SPC_XIO_PULSEGEN2_LEN,
    SPC_XIO_PULSEGEN2_LOOPS,
    SPC_XIO_PULSEGEN2_MODE,
    SPC_XIO_PULSEGEN3_CONFIG,
    SPC_XIO_PULSEGEN3_HIGH,
    SPC_XIO_PULSEGEN3_LEN,
    SPC_XIO_PULSEGEN3_LOOPS,
    SPC_XIO_PULSEGEN3_MODE,
    SPC_XIO_PULSEGEN_AVAILHIGH_MAX,
    SPC_XIO_PULSEGEN_AVAILHIGH_MIN,
    SPC_XIO_PULSEGEN_AVAILHIGH_STEP,
    SPC_XIO_PULSEGEN_AVAILLEN_MAX,
    SPC_XIO_PULSEGEN_AVAILLEN_MIN,
    SPC_XIO_PULSEGEN_AVAILLEN_STEP,
    SPC_XIO_PULSEGEN_AVAILLOOPS_MAX,
    SPC_XIO_PULSEGEN_AVAILLOOPS_MIN,
    SPC_XIO_PULSEGEN_AVAILLOOPS_STEP,
    SPC_XIO_PULSEGEN_CLOCK,
    SPC_XIO_PULSEGEN_ENABLE,
)
from spectrumdevice.devices.abstract_device import AbstractSpectrumDevice, AbstractSpectrumCard, AbstractSpectrumStarHub
from spectrumdevice.devices.awg.abstract_spectrum_awg import AbstractSpectrumAWG
from spectrumdevice.devices.digitiser.abstract_spectrum_digitiser import AbstractSpectrumDigitiser
from spectrumdevice.devices.mocks.mock_waveform_source import mock_waveform_source_factory
from spectrumdevice.exceptions import MockRegisterNotImplemented, SpectrumDeviceNotConnected
from spectrumdevice.settings import (
    AcquisitionMode,
    AdvancedCardFeature,
    CardFeature,
    ModelNumber,
    SpectrumRegisterLength,
)
from spectrumdevice.settings.card_dependent_properties import CardType
from spectrumdevice.settings.device_modes import GenerationMode


class MockAbstractSpectrumDevice(AbstractSpectrumDevice, ABC):
    def __init__(self, param_dict: Optional[Dict[int, int]], **kwargs: Any):
        if param_dict is None:
            self._param_dict: Dict[int, int] = {}
        else:
            self._param_dict = param_dict
        super().__init__(**kwargs)  # required for proper MRO resolution

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
                raise MockRegisterNotImplemented(
                    f"Register {spectrum_register} has not been implemented in the mock device."
                )
        else:
            raise SpectrumDeviceNotConnected("Mock device has been disconnected.")


class MockAbstractSpectrumCard(MockAbstractSpectrumDevice, AbstractSpectrumCard, ABC):
    """Overrides methods of `AbstractSpectrumDevice` that communicate with hardware with mocked implementations, allowing
    software to be tested without Spectrum hardware connected or drivers installed, e.g. during CI. Instances of this
    class cannot be constructed directly - instantiate `MockAbstractSpectrumDigitiser` and `MockSpectrumStarHub` objects instead,
    which inherit from this class."""

    def __init__(
        self,
        model: ModelNumber,
        card_type: CardType,
        mode: Union[AcquisitionMode, GenerationMode],
        num_modules: int,
        num_channels_per_module: int,
        card_features: list[CardFeature],
        advanced_card_features: list[AdvancedCardFeature],
        **kwargs: Any,
    ) -> None:
        param_dict: dict[int, int] = {}
        param_dict[SPC_PCIFEATURES] = reduce(or_, [f.value for f in card_features]) if card_features else 0
        param_dict[SPC_PCIEXTFEATURES] = (
            reduce(or_, [f.value for f in advanced_card_features]) if advanced_card_features else 0
        )
        param_dict[SPCM_X0_AVAILMODES] = SPCM_XMODE_DISABLE
        param_dict[SPCM_X1_AVAILMODES] = SPCM_XMODE_DISABLE
        param_dict[SPCM_X2_AVAILMODES] = SPCM_XMODE_DISABLE
        param_dict[SPCM_X3_AVAILMODES] = SPCM_XMODE_DISABLE
        param_dict[SPC_XIO_PULSEGEN_CLOCK] = 1000
        param_dict[SPC_TIMEOUT] = 1000
        param_dict[SPC_SEGMENTSIZE] = 1000
        param_dict[SPC_MEMSIZE] = 1000
        param_dict[SPC_PCITYP] = model.value
        param_dict[SPC_FNCTYPE] = card_type.value
        param_dict[SPC_CARDMODE] = cast(int, mode.value)  # cast suppresses a pycharm warning
        param_dict[SPC_MIINST_MODULES] = num_modules
        param_dict[SPC_MIINST_CHPERMODULE] = num_channels_per_module
        param_dict[SPC_MIINST_BYTESPERSAMPLE] = 2
        param_dict[SPC_MIINST_MAXADCVALUE] = 128
        # Pulse generation:
        param_dict[SPC_XIO_PULSEGEN_ENABLE] = 0
        param_dict[SPC_XIO_PULSEGEN0_CONFIG] = 0
        param_dict[SPC_XIO_PULSEGEN1_CONFIG] = 0
        param_dict[SPC_XIO_PULSEGEN2_CONFIG] = 0
        param_dict[SPC_XIO_PULSEGEN3_CONFIG] = 0
        param_dict[SPC_XIO_PULSEGEN0_MODE] = SPCM_PULSEGEN_MODE_GATED
        param_dict[SPC_XIO_PULSEGEN1_MODE] = SPCM_PULSEGEN_MODE_GATED
        param_dict[SPC_XIO_PULSEGEN2_MODE] = SPCM_PULSEGEN_MODE_GATED
        param_dict[SPC_XIO_PULSEGEN3_MODE] = SPCM_PULSEGEN_MODE_GATED
        # ...pulse period
        param_dict[SPC_XIO_PULSEGEN_AVAILLEN_MIN] = 2
        param_dict[SPC_XIO_PULSEGEN_AVAILLEN_MAX] = 1000
        param_dict[SPC_XIO_PULSEGEN_AVAILLEN_STEP] = 2
        param_dict[SPC_XIO_PULSEGEN0_LEN] = 2
        param_dict[SPC_XIO_PULSEGEN1_LEN] = 2
        param_dict[SPC_XIO_PULSEGEN2_LEN] = 2
        param_dict[SPC_XIO_PULSEGEN3_LEN] = 2
        # ...pulse high voltage duration
        param_dict[SPC_XIO_PULSEGEN_AVAILHIGH_MIN] = 1
        param_dict[SPC_XIO_PULSEGEN_AVAILHIGH_MAX] = 500
        param_dict[SPC_XIO_PULSEGEN_AVAILHIGH_STEP] = 1
        param_dict[SPC_XIO_PULSEGEN0_HIGH] = 1
        param_dict[SPC_XIO_PULSEGEN1_HIGH] = 1
        param_dict[SPC_XIO_PULSEGEN2_HIGH] = 1
        param_dict[SPC_XIO_PULSEGEN3_HIGH] = 1
        # ...number of pulses
        param_dict[SPC_XIO_PULSEGEN_AVAILLOOPS_MIN] = 1
        param_dict[SPC_XIO_PULSEGEN_AVAILLOOPS_MAX] = 1000
        param_dict[SPC_XIO_PULSEGEN_AVAILLOOPS_STEP] = 1
        param_dict[SPC_XIO_PULSEGEN0_LOOPS] = 0
        param_dict[SPC_XIO_PULSEGEN1_LOOPS] = 0
        param_dict[SPC_XIO_PULSEGEN2_LOOPS] = 0
        param_dict[SPC_XIO_PULSEGEN3_LOOPS] = 0
        # ...trigger delay
        param_dict[602007] = 0  # SPC_XIO_PULSEGEN_AVAILDELAY_MIN not in regs for some reason
        param_dict[602008] = 1000000  # SPC_XIO_PULSEGEN_AVAILDELAY_MAX not in regs for some reason
        param_dict[602009] = 1  # SPC_XIO_PULSEGEN_AVAILDELAY_STEP not in regs for some reason
        param_dict[601003] = 0  # SPC_XIO_PULSEGEN0_DELAY not in regs for some reason
        param_dict[601103] = 0  # SPC_XIO_PULSEGEN1_DELAY not in regs for some reason
        param_dict[601203] = 0  # SPC_XIO_PULSEGEN2_DELAY not in regs for some reason
        param_dict[601303] = 0  # SPC_XIO_PULSEGEN3_DELAY not in regs for some reason
        # Channel settings
        param_dict[SPC_AMP0] = 200
        param_dict[SPC_AMP1] = 200
        param_dict[SPC_AMP2] = 200
        param_dict[SPC_AMP3] = 200
        param_dict[SPC_AMP4] = 200
        param_dict[SPC_AMP5] = 200
        param_dict[SPC_AMP6] = 200
        param_dict[SPC_AMP7] = 200
        param_dict[SPC_AMP8] = 200
        param_dict[SPC_AMP9] = 200
        param_dict[SPC_AMP10] = 200
        param_dict[SPC_AMP11] = 200
        param_dict[SPC_AMP12] = 200
        param_dict[SPC_AMP13] = 200
        param_dict[SPC_AMP14] = 200
        param_dict[SPC_AMP15] = 200
        param_dict[SPC_OFFS0] = 0
        param_dict[SPC_OFFS1] = 0
        param_dict[SPC_OFFS2] = 0
        param_dict[SPC_OFFS3] = 0
        param_dict[SPC_OFFS4] = 0
        param_dict[SPC_OFFS5] = 0
        param_dict[SPC_OFFS6] = 0
        param_dict[SPC_OFFS7] = 0
        param_dict[SPC_OFFS8] = 0
        param_dict[SPC_OFFS9] = 0
        param_dict[SPC_OFFS10] = 0
        param_dict[SPC_OFFS11] = 0
        param_dict[SPC_OFFS12] = 0
        param_dict[SPC_OFFS13] = 0
        param_dict[SPC_OFFS14] = 0
        param_dict[SPC_OFFS15] = 0

        self._buffer_lock = Lock()
        self._enabled_channels = [0]
        super().__init__(
            param_dict=param_dict, **kwargs
        )  # then call the rest of the inits after the params have been set
        self._visa_string = "/mock" + self._visa_string


class MockAbstractSpectrumStarHub(MockAbstractSpectrumDevice, AbstractSpectrumStarHub, ABC):
    pass


class MockAbstractSpectrumDigitiser(MockAbstractSpectrumDevice, AbstractSpectrumDigitiser, ABC):
    """Overrides methods of `AbstractSpectrumDigitiser` that communicate with hardware with mocked implementations, allowing
    software to be tested without Spectrum hardware connected or drivers installed, e.g. during CI. Instances of this
    class cannot be constructed directly - instantiate `MockAbstractSpectrumDigitiser` and `MockSpectrumStarHub` objects instead,
    which inherit from this class."""

    def __init__(self, mock_source_frame_rate_hz: float = 10.0, **kwargs: Any) -> None:
        """
        Args:
            source_frame_rate_hz (float): Frame rate at which a mock waveform source will generate waveforms.
        """
        # use super() to ensure init of MockAbstractSpectrumDevice is only called once in child classes with multiple
        # inheritance
        super().__init__(mode=AcquisitionMode.SPC_REC_STD_SINGLE, **kwargs)
        self._source_frame_rate_hz = mock_source_frame_rate_hz
        self._buffer_lock = Lock()
        self._acquisition_stop_event = Event()
        self._acquisition_thread: Optional[Thread] = None
        self._timestamp_thread: Optional[Thread] = None
        self._enabled_channels = [0]

    def start(self) -> None:
        """Starts a mock waveform source in a separate thread. The source generates noise samples according to the
        number of currently enabled channels and the acquisition length, and places them in the transfer buffer.
        """
        self.define_transfer_buffer()
        notify_size = self.transfer_buffers[0].notify_size_in_pages  # this will be 0 in STD_SINGLE_MODE
        waveform_source = mock_waveform_source_factory(self.acquisition_mode, self._param_dict, notify_size)
        amplitude = self.read_spectrum_device_register(SPC_MIINST_MAXADCVALUE)
        print(f"STARTING MOCK WAVEFORMS SOURCE WITH AMPLITUDE {amplitude}")
        self._acquisition_stop_event.clear()
        self._acquisition_thread = Thread(
            target=waveform_source,
            args=(
                self._acquisition_stop_event,
                self._source_frame_rate_hz,
                amplitude,
                self.transfer_buffers[0].data_array,
                self.acquisition_length_in_samples * len(self.enabled_analog_channels),
                self._buffer_lock,
            ),
        )
        self._acquisition_thread.start()

    def stop(self) -> None:
        """Stops the mock waveform source and timestamp threads."""
        self._acquisition_stop_event.set()


class MockAbstractSpectrumAWG(MockAbstractSpectrumDevice, AbstractSpectrumAWG, ABC):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(mode=GenerationMode.SPC_REP_STD_SINGLE, **kwargs)
