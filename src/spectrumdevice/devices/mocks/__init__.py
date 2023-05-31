"""Provides Mock spectrum device classes for testing software when no drivers or hardware are present."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

import logging
from abc import ABC, abstractmethod
from threading import Event, Lock, Thread
from time import sleep, monotonic
from typing import Optional, Sequence, List

from numpy import ndarray, zeros
from numpy.random import uniform

from spectrumdevice.devices.mocks.timestamps import MockTimestamper
from spectrumdevice.devices.spectrum_card import SpectrumCard
from spectrumdevice.devices.spectrum_device import SpectrumDevice
from spectrumdevice.exceptions import (
    SpectrumDeviceNotConnected,
    SpectrumNoTransferBufferDefined,
    SpectrumSettingsMismatchError,
)
from spectrumdevice.settings import SpectrumRegisterLength
from spectrumdevice.settings.card_dependent_properties import CardType
from spectrumdevice.settings.device_modes import AcquisitionMode
from spectrumdevice.settings.transfer_buffer import CardToPCDataTransferBuffer
from spectrumdevice.devices.spectrum_star_hub import SpectrumStarHub
from spectrum_gmbh.regs import (
    SPC_MIINST_MODULES,
    SPC_MIINST_CHPERMODULE,
    SPC_PCIFEATURES,
    SPCM_X0_AVAILMODES,
    SPCM_X1_AVAILMODES,
    SPCM_X2_AVAILMODES,
    SPCM_X3_AVAILMODES,
    SPCM_XMODE_DISABLE,
    SPCM_FEAT_MULTI,
    SPC_PCIEXTFEATURES,
    SPCM_FEAT_EXTFW_SEGSTAT,
    SPC_TIMEOUT,
    SPC_SEGMENTSIZE,
    SPC_MEMSIZE,
    SPC_CARDMODE,
    SPC_PCITYP,
    SPC_MIINST_MAXADCVALUE,
)

logger = logging.getLogger(__name__)


class MockSpectrumDevice(SpectrumDevice, ABC):
    """Overrides methods of `SpectrumDevice` that communicate with hardware with mocked implementations, allowing
    software to be tested without Spectrum hardware connected or drivers installed, e.g. during CI. Instances of this
    class cannot be constructed directly - instantiate `MockSpectrumDevice` and `MockSpectrumStarHub` objects instead,
    which inherit from this class."""

    def __init__(self, source_frame_rate_hz: float = 10.0) -> None:
        """
        Args:
            source_frame_rate_hz (float): Frame rate at which a mock waveform source will generate waveforms.
        """
        self._source_frame_rate_hz = source_frame_rate_hz
        self._param_dict = {
            SPC_PCIFEATURES: SPCM_FEAT_MULTI,
            SPC_PCIEXTFEATURES: SPCM_FEAT_EXTFW_SEGSTAT,
            SPCM_X0_AVAILMODES: SPCM_XMODE_DISABLE,
            SPCM_X1_AVAILMODES: SPCM_XMODE_DISABLE,
            SPCM_X2_AVAILMODES: SPCM_XMODE_DISABLE,
            SPCM_X3_AVAILMODES: SPCM_XMODE_DISABLE,
            SPC_TIMEOUT: 1000,
            SPC_SEGMENTSIZE: 1000,
            SPC_MEMSIZE: 1000,
            SPC_CARDMODE: AcquisitionMode.SPC_REC_STD_SINGLE.value,
            SPC_MIINST_MAXADCVALUE: 128,
        }

        self._buffer_lock = Lock()
        self._acquisition_stop_event = Event()
        self._acquisition_thread: Optional[Thread] = None
        self._timestamp_thread: Optional[Thread] = None
        self._enabled_channels = [0]
        self._on_device_buffer: ndarray = zeros(1000)
        self._previous_data = self._on_device_buffer.copy()

    def start_acquisition(self) -> None:
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

    def stop_acquisition(self) -> None:
        """Stops the mock waveform source and timestamp threads."""
        self._acquisition_stop_event.set()

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


class MockSpectrumCard(SpectrumCard, MockSpectrumDevice):
    """A mock spectrum card, for testing software written to use the `SpectrumCard` class.

    This class overrides methods of `SpectrumCard` that communicate with hardware with mocked implementations, allowing
    software to be tested without Spectrum hardware connected or drivers installed, e.g. during CI. It overrides
    methods to use to set up a mock 'on device buffer' attribute into which a mock waveform source will write
    samples. It also uses a MockTimestamper to generated timestamps for mock waveforms.
    """

    def __init__(
        self,
        device_number: int,
        card_type: CardType,
        mock_source_frame_rate_hz: float,
        num_modules: int = 2,
        num_channels_per_module: int = 4,
    ):
        """
        Args:
            device_number (int): The index of the mock device to create. Used to create a name for the device which is
                used internally.
            card_type (CardType): The model of card to mock. Affects the allowed acquisition and post-trigger lengths.
            mock_source_frame_rate_hz (float): Rate at which waveforms will be generated by the mock source providing
                data to the mock spectrum card.
            num_modules (int): The number of internal modules to assign the mock card. Default 2. On real hardware, this
                is read from the device so does not need to be set. See the Spectrum documentation to work out how many
                modules your hardware has.
            num_channels_per_module (int): The number of channels per module. Default 4 (so 8 channels in total). On
                real hardware, this is read from the device so does not need to be set.
        """
        MockSpectrumDevice.__init__(self, mock_source_frame_rate_hz)
        self._param_dict[SPC_MIINST_MODULES] = num_modules
        self._param_dict[SPC_MIINST_CHPERMODULE] = num_channels_per_module
        self._param_dict[SPC_PCITYP] = card_type.value
        SpectrumCard.__init__(self, device_number=device_number)
        self._visa_string = f"MockCard{device_number}"
        self._connect(self._visa_string)
        self._acquisition_mode = self.acquisition_mode

    def enable_timestamping(self) -> None:
        self._timestamper: MockTimestamper = MockTimestamper(self, self._handle)

    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        """Mock timestamper needs to be recreated if the acquisition mode is changed."""
        super().set_acquisition_mode(mode)
        self._timestamper = MockTimestamper(self, self._handle)

    def set_sample_rate_in_hz(self, rate: int) -> None:
        """Mock timestamper needs to be recreated if the sample rate is changed."""
        super().set_sample_rate_in_hz(rate)
        self._timestamper = MockTimestamper(self, self._handle)

    def set_acquisition_length_in_samples(self, length_in_samples: int) -> None:
        """Set length of mock recording (per channel). In FIFO mode, this will be quantised to the nearest 8 samples.
        See `SpectrumCard` for more information. This method is overridden here only so that the internal attributes
        related to the mock on-device buffer can be set.

        Args:
            length_in_samples (int): Number of samples in each generated mock waveform
        """
        self._on_device_buffer = zeros(length_in_samples * len(self.enabled_channels))
        self._previous_data = zeros(length_in_samples * len(self.enabled_channels))
        super().set_acquisition_length_in_samples(length_in_samples)

    def set_enabled_channels(self, channels_nums: List[int]) -> None:
        """Set the channels to enable for the mock acquisition. See `SpectrumCard` for more information. This method is
        overridden here only so that the internal attributes related to the mock on-device buffer can be set.

        Args:
            channels_nums (List[int]): List of mock channel indices to enable, e.g. [0, 1, 2].

        """
        if len(list(filter(lambda x: 0 <= x < len(self.channels), channels_nums))) == len(channels_nums):
            self._on_device_buffer = zeros(self.acquisition_length_in_samples * len(channels_nums))
            self._previous_data = zeros(self.acquisition_length_in_samples * len(channels_nums))
            super().set_enabled_channels(channels_nums)
        else:
            raise SpectrumSettingsMismatchError("Not enough channels in mock device configuration.")

    def define_transfer_buffer(self, buffer: Optional[List[CardToPCDataTransferBuffer]] = None) -> None:
        """Create or provide a `CardToPCDataTransferBuffer` object into which samples from the mock 'on device buffer'
        will be transferred. If none is provided, a buffer will be instantiated using the currently set acquisition
        length and the number of enabled channels.

        Args:
            buffer (Optional[List[`CardToPCDataTransferBuffer`]]): A length-1 list containing a
            `CardToPCDataTransferBuffer` object.
        """
        if buffer:
            self._transfer_buffer = buffer[0]
        else:
            self._transfer_buffer = CardToPCDataTransferBuffer(
                self.acquisition_length_in_samples * len(self.enabled_channels)
            )

    def start_transfer(self) -> None:
        """See `SpectrumCard.start_transfer()`. This mock implementation simulates the continuous transfer of samples
        from the mock 'on device buffer' to the transfer buffer by pointing the transfer buffer's data buffer attribute
        to the mock on-device buffer."""
        if self._transfer_buffer:
            self._transfer_buffer.data_array = self._on_device_buffer
        else:
            raise SpectrumNoTransferBufferDefined("Call define_transfer_buffer method.")

    def stop_transfer(self) -> None:
        """See `SpectrumCard.stop_transfer()`. This mock implementation simulates the end of the continuous transfer of
        samples from the mock 'on device buffer' to the transfer buffer by assigning the transfer bugger to an array of
        zeros."""
        if self._transfer_buffer:
            self._transfer_buffer.data_array = zeros(self._transfer_buffer.data_array.shape)
        else:
            raise SpectrumNoTransferBufferDefined("Call define_transfer_buffer method.")

    def wait_for_transfer_to_complete(self) -> None:
        """See `SpectrumCard.wait_for_transfer_to_complete()`. This mock implementation blocks until a new mock transfer
        has been completed (i.e. the contents of the transfer buffer has changed since __init__() or since the last call
        to `wait_for_transfer_to_complete()`)."""
        if self._transfer_buffer:
            while (self._previous_data == self._transfer_buffer.data_array).all():
                sleep(0.01)
            self._previous_data = self._transfer_buffer.data_array.copy()
        else:
            raise SpectrumNoTransferBufferDefined("No transfer in progress.")

    def wait_for_acquisition_to_complete(self) -> None:
        """See `SpectrumCard.wait_for_acquisition_to_complete()`. This mock implementation blocks until a mock
        acquisition has been completed (i.e. the acquisition thread has shut down) or the request has timed out
        according to the `self.timeout_ms attribute`."""
        if self._acquisition_thread is not None:
            self._acquisition_thread.join(timeout=1e-3 * self.timeout_in_ms)
            if self._acquisition_thread.is_alive():
                logger.warning("A timeout occurred while waiting for mock acquisition to complete.")
        else:
            logger.warning("No acquisition in progress. Wait for acquisition to complete has no effect")


class MockSpectrumStarHub(SpectrumStarHub, MockSpectrumDevice):
    """A mock spectrum StarHub, for testing software written to use the `SpectrumStarHub` class.

    Overrides methods of `SpectrumStarHub` and `SpectrumDevice` that communicate with hardware with mocked
    implementations allowing software to be tested without Spectrum hardware connected or drivers installed, e.g. during
    CI."""

    def __init__(
        self,
        device_number: int,
        child_cards: Sequence[MockSpectrumCard],
        master_card_index: int,
    ):
        """
        Args:
            child_cards (Sequence[`MockSpectrumCard`]): A list of `MockSpectrumCard` objects defining the properties of
            the child cards located within the mock hub.
            master_card_index (int): The position within child_cards where the master card (the card which controls the
                clock) is located.
        """
        MockSpectrumDevice.__init__(self)
        SpectrumStarHub.__init__(self, device_number, child_cards, master_card_index)
        self._visa_string = f"MockHub{device_number}"
        self._connect(self._visa_string)
        self._acquisition_mode = self.acquisition_mode

    def start_acquisition(self) -> None:
        """Start a mock acquisition

        See `SpectrumStarHub.start_acquisition()`. With a hardware device, StarHub's only need to be sent a single
        instruction to start acquisition, which they automatically relay to their child cards - hence why
        `start_acquisition` is implemented in SpectrumDevice (base class to both `SpectrumCard` and `SpectrumStarHub`)
        rather than in `SpectrumStarHub`. In this mock `implementation`, each card's acquisition is started
        individually.

        """
        for card in self._child_cards:
            card.start_acquisition()

    def stop_acquisition(self) -> None:
        """Stop a mock acquisition

        See `SpectrumDevice.stop_acquisition`. With a hardware device, StarHub's only need to be sent a single
        instruction to stop acquisition, which they automatically relay to their child cards - hence why
        `stop_acquisition()` is implemented in SpectrumDevice (base class to both `SpectrumCard` and `SpectrumStarHub`)
        rather than in `SpectrumStarHub`. In this mock implementation, each card's acquisition is stopped individually.

        """
        for card in self._child_cards:
            card.stop_acquisition()


class MockWaveformSource(ABC):
    """Interface for a mock noise waveform source. Implementations are intended to be called in their own thread.
    When called, `MockWaveformSource` implementations will fill a provided buffer with noise samples."""

    @abstractmethod
    def __call__(
        self, stop_flag: Event, frame_rate: float, amplitude: float, on_device_buffer: ndarray, buffer_lock: Lock
    ) -> None:
        raise NotImplementedError()


class SingleModeMockWaveformSource(MockWaveformSource):
    def __call__(
        self, stop_flag: Event, frame_rate: float, amplitude: float, on_device_buffer: ndarray, buffer_lock: Lock
    ) -> None:
        """When called, this MockWaveformSource simulates SPC_REC_STD_SINGLE Mode, placing a single frames worth of
        samples into a provided mock on_device_buffer.

        Args:
            stop_flag (Event): A threading event that will be used in the calling thread to stop the acquisition.
            frame_rate (float): The samples will be generated 1 / frame_rate seconds after __call__ is called.
            amplitude (float): Waveforms will contain random values in the range -amplitude to +amplitude
            on_device_buffer (ndarray): The numpy array into which the noise samples will be written.
            buffer_lock (Lock): A threading lock created in the calling thread that will be used to ensure access to
                the on_device_buffer array is thread safe.

        """
        start_time = monotonic()
        while not stop_flag.is_set() and ((monotonic() - start_time) < (1 / frame_rate)):
            sleep(0.001)
        if not stop_flag.is_set():
            with buffer_lock:
                on_device_buffer[:] = uniform(low=-1 * amplitude, high=amplitude, size=len(on_device_buffer))


class MultiFIFOModeMockWaveformSource(MockWaveformSource):
    def __call__(
        self, stop_flag: Event, frame_rate: float, amplitude: float, on_device_buffer: ndarray, buffer_lock: Lock
    ) -> None:
        """When called, this `MockWaveformSource` simulates SPC_REC_FIFO_MULTI Mode, continuously replacing the contents
        of on_device_buffer with new frames of noise samples.

        Args:
            stop_flag (Event): A threading event that will be used in the calling thread to stop the acquisition.
            frame_rate (float): The contents of the on_device_buffer will be updated at this rate (Hz).
            amplitude (float): Waveforms will contain random values from a uniform distribution in the range -amplitude
            to +amplitude
            on_device_buffer (ndarray): The numpy array into which the noise samples will be written.
            buffer_lock (Lock): A threading lock created in the calling thread that will be used to ensure access to
                the on_device_buffer array is thread safe.

        """
        while not stop_flag.is_set():
            with buffer_lock:
                on_device_buffer[:] = uniform(low=-1 * amplitude, high=amplitude, size=len(on_device_buffer))
                sleep(1 / frame_rate)


def mock_waveform_source_factory(acquisition_mode: AcquisitionMode) -> MockWaveformSource:
    if acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
        return MultiFIFOModeMockWaveformSource()
    elif AcquisitionMode.SPC_REC_STD_SINGLE:
        return SingleModeMockWaveformSource()
    else:
        raise NotImplementedError(f"Mock waveform source not yet implemented for {acquisition_mode} acquisition mode.")
