from abc import ABC, abstractmethod
from threading import Event, Lock, Thread
from time import sleep, monotonic
from typing import Optional, Sequence, List

from numpy import ndarray, zeros
from numpy.random import randn

from pyspecde.hardware_model.spectrum_card import SpectrumCard
from pyspecde.hardware_model.spectrum_device import SpectrumDevice
from pyspecde.exceptions import (
    SpectrumDeviceNotConnected,
    SpectrumNoTransferBufferDefined,
    SpectrumSettingsMismatchError,
)
from pyspecde.hardware_model.spectrum_interface import SpectrumIntLengths
from pyspecde.spectrum_api_wrapper import AcquisitionMode
from pyspecde.spectrum_api_wrapper.transfer_buffer import TransferBuffer, transfer_buffer_factory
from pyspecde.hardware_model.spectrum_star_hub import SpectrumStarHub
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
)


class MockSpectrumDevice(SpectrumDevice, ABC):
    def __init__(self, source_frame_rate_hz: float = 10.0) -> None:
        """MockSpectrumDevice

        Overrides methods of SpectrumDevice that communicate with hardware with mocked implementations, allowing
        software to be tested without Spectrum hardware connected or drivers installed, e.g. during CI.

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
        }

        self._buffer_lock = Lock()
        self._acquisition_stop_event = Event()
        self._acquisition_thread: Optional[Thread] = None
        self._enabled_channels = [0]
        self._on_device_buffer: ndarray = zeros(1000)
        self._previous_data = self._on_device_buffer.copy()

    def start_acquisition(self) -> None:
        """start_acquisition

        Starts a mock waveform source in a separate thread. The source generates noise samples according to the
        number of currently enabled channels and the acquisition length, and places them in the virtual on device buffer
        (the _on_device_buffer attribute).

        """
        target = mock_waveform_source_factory(self.acquisition_mode)
        self._acquisition_stop_event.clear()
        self._acquisition_thread = Thread(
            target=target,
            args=(self._acquisition_stop_event, self._source_frame_rate_hz, self._on_device_buffer, self._buffer_lock),
        )
        self._acquisition_thread.start()

    def stop_acquisition(self) -> None:
        """stop_acquisition

        Stops the mock waveform source thread.

        """
        self._acquisition_stop_event.set()

    def set_spectrum_api_param(
        self, spectrum_register: int, value: int, length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO
    ) -> None:
        """set_spectrum_api_param

        Simulates the setting of a parameter or command (register) on Spectrum hardware by storing its value in the
        _param_dict dictionary.

        Args:
            spectrum_register (int): Mock Spectrum device register to set. Should be imported from regs.py, which is
                part of the spectrum_gmbh package written by Spectrum.
            value (int): Value to set the register to. Should be imported from regs.py, which is
                part of the spectrum_gmbh package written by Spectrum, or taken from one of the Enums provided by
                the spectrum_api_wrapper package.
            length (SpectrumIntLengths): Length in bits of the register being set. Either
                SpectrumIntLengths.THIRTY_TWO or SpectrumIntLengths.SIXTY_FOUR. Check the Spectrum documentation for
                the register being set to determine the length to use. Default is 32 bit which is correct for the
                majority of cases.
        """
        if self.connected:
            self._param_dict[spectrum_register] = value
        else:
            raise SpectrumDeviceNotConnected("Mock device has been disconnected.")

    def get_spectrum_api_param(
        self, spectrum_register: int, length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO
    ) -> int:
        """get_spectrum_api_param

        Read the current value of a mock Spectrum register. Registers that do not appear in the initial assignment of
        the _param_dict attribute in __init__() will need to be set using set_spectrum_api_param() before they can be
        read.

        Args:
            spectrum_register (int): Mck spectrum device register to read. Should be imported from regs.py, which is
                part pf the spectrum_gmbh package written by Spectrum, or taken from one of the Enums provided by
                the spectrum_api_wrapper package.
            length (SpectrumIntLengths): Length in bits of the register being read. Either
                SpectrumIntLengths.THIRTY_TWO or SpectrumIntLengths.SIXTY_FOUR. Check the Spectrum documentation for
                the register to determine the length to use. Default is 32 bit which is correct for the majority of
                cases.

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
    def __init__(self, mock_source_frame_rate_hz: float, num_modules: int = 2, num_channels_per_module: int = 4):
        """MockSpectrumDevice

        Overrides methods of SpectrumCard that communicate with hardware with mocked implementations, allowing
        software to be tested without Spectrum hardware connected or drivers installed, e.g. during CI. Also overrides
        methods used to set up a mock 'on device buffer' attribute into which a mock waveform source will write
        samples.

        Args:
            mock_source_frame_rate_hz (float): Rate at which waveforms will be generated by the mock source providing data
                to the mock spectrum card.
            num_modules (int): The number of internal modules to assign the mock card. Default 2.
            num_channels_per_module (int): The number of channels per module. Default 4 (so 8 channels in total).
        """
        MockSpectrumDevice.__init__(self, mock_source_frame_rate_hz)
        self._param_dict[SPC_MIINST_MODULES] = num_modules
        self._param_dict[SPC_MIINST_CHPERMODULE] = num_channels_per_module
        SpectrumCard.__init__(self, device_number=0)

    def set_acquisition_length_samples(self, length_in_samples: int) -> None:
        """set_acquisition_length_samples

        Args:
            length_in_samples (int): Number of samples in each generated mock waveform

        """
        self._on_device_buffer = zeros(length_in_samples * len(self.enabled_channels))
        self._previous_data = zeros(length_in_samples * len(self.enabled_channels))
        super().set_acquisition_length_samples(length_in_samples)

    def set_enabled_channels(self, channels_nums: List[int]) -> None:
        """set_enabled_channels

        Args:
            channels_nums (List[int]): List of mock channel indices to enable, e.g. [0, 1, 2].

        """
        if len(list(filter(lambda x: 0 <= x < len(self.channels), channels_nums))) == len(channels_nums):
            self._on_device_buffer = zeros(self.acquisition_length_samples * len(channels_nums))
            self._previous_data = zeros(self.acquisition_length_samples * len(channels_nums))
            super().set_enabled_channels(channels_nums)
        else:
            raise SpectrumSettingsMismatchError("Not enough channels in mock device configuration.")

    def define_transfer_buffer(self, buffer: Optional[TransferBuffer] = None) -> None:
        """define_transfer_buffer

        Creates a TransferBuffer object into which samples from the mock 'on device buffer' will be transferred.

        Args:
            buffer (Optional[TransferBuffer]): TransferBuffer object. If None is provided, a buffer will be
                instantiated using the currently set acquisition length and the number of enabled channels.

        """
        if buffer:
            self._transfer_buffer = buffer
        else:
            self._transfer_buffer = transfer_buffer_factory(
                self.acquisition_length_samples * len(self.enabled_channels)
            )

    def start_transfer(self) -> None:
        """start_transfer

        Simulates the continuous transfer of samples from the mock 'on device buffer' to the transfer buffer by pointing
            the transfer buffer's databuffer attribute to the on device buffer.

        """
        if self._transfer_buffer:
            self._transfer_buffer.data_buffer = self._on_device_buffer
        else:
            raise SpectrumNoTransferBufferDefined("Call define_transfer_buffer method.")

    def stop_transfer(self) -> None:
        """stop_transfer

        Simulates the end of the continuous transfer of samples from the mock 'on device buffer' to the transfer buffer
        by assigning the transfer bugger to an array of zeros.

        """
        if self._transfer_buffer:
            self._transfer_buffer.data_buffer = zeros(self._transfer_buffer.data_buffer.shape)
        else:
            raise SpectrumNoTransferBufferDefined("Call define_transfer_buffer method.")

    def wait_for_transfer_to_complete(self) -> None:
        """wait_for_transfer_to_complete

        Blocks until a new mock transfer has been completed (i.e. the contents of the transfer buffer has changed since
            __init__() or since the last call to wait_for_transfer_to_complete).

        """
        if self._transfer_buffer:
            while (self._previous_data == self._transfer_buffer.data_buffer).all():
                sleep(0.01)
            self._previous_data = self._transfer_buffer.data_buffer.copy()
        else:
            raise SpectrumNoTransferBufferDefined("No transfer in progress.")

    def wait_for_acquisition_to_complete(self) -> None:
        """wait_for_acquisition_to_complete

        Blocks until a mock acquisition has been completed (i.e. the acquisition thread has shut down) or the request
            has timed out according to the self.timeout_ms attribute.

        """
        if self._acquisition_thread is not None:
            self._acquisition_thread.join(timeout=1e-3 * self.timeout_ms)
            if self._acquisition_thread.is_alive():
                print("A timeout occurred while waiting for mock acquisition to complete.")
        else:
            print("No acquisition in progress.")


class MockSpectrumStarHub(SpectrumStarHub, MockSpectrumDevice):
    def __init__(
        self,
        child_cards: Sequence[MockSpectrumCard],
        master_card_index: int,
    ):
        """MockSpectrumStarHub

        Overrides methods of SpectrumStarHub and SpectrumDevice that communicate with hardware with mocked
        implementations, allowing software to be tested without Spectrum hardware connected or drivers installed,
        e.g. during CI.

        Args:
            child_cards (Sequence[MockSpectrumCard]): A list of MockSpectrumCard objects defining the properties of the
                child cards located within the mock hub.
            master_card_index (int): The position within child_cards where the master card (the card which controls the
                clock) is located.
        """
        MockSpectrumDevice.__init__(self)
        SpectrumStarHub.__init__(self, 0, child_cards, master_card_index)

    def start_acquisition(self) -> None:
        """start_acquisition

        This method overrides SpectrumDevice.start_acquisition. In reality, StarHub's only need to be sent a single
        instruction to start acquisition, which they automatically relay to their child cards - hence why
        start_acquisition is implemented in SpectrumDevice (base class to both SpectrumCard and SpectrumStarHub) rather
        than in SpectrumStarHub. For the mock implementation, each card's acquisition is started individually.

        """
        for card in self._child_cards:
            card.start_acquisition()

    def stop_acquisition(self) -> None:
        """stop_acquisition

        This method overrides SpectrumDevice.stop_acquisition. In reality, StarHub's only need to be sent a single
        instruction to stop acquisition, which they automatically relay to their child cards - hence why
        stop_acquisition is implemented in SpectrumDevice (base class to both SpectrumCard and SpectrumStarHub) rather
        than in SpectrumStarHub. For the mock implementation, each card's acquisition is stopped individually.

        """
        for card in self._child_cards:
            card.stop_acquisition()


class MockWaveformSource(ABC):
    """Interface for a mock noise waveform source. Implementations are intended to be called in their own thread.
    When called, MockWaveformSource implementations will fill a provided buffer with noise samples."""

    @abstractmethod
    def __call__(self, stop_flag: Event, frame_rate: float, on_device_buffer: ndarray, buffer_lock: Lock) -> None:
        raise NotImplementedError()


class SingleModeMockWaveformSource(MockWaveformSource):
    def __call__(self, stop_flag: Event, frame_rate: float, on_device_buffer: ndarray, buffer_lock: Lock) -> None:
        """SingleModeMockWaveformSource

        When called, this MockWaveformSource simulates SPC_REC_STD_SINGLE Mode, placing a single frames worth of samples
        into a provided mock on_device_buffer.

        Args:
            stop_flag (Event): A threading event that will be used in the calling thread to stop the acquisition.
            frame_rate (float): The samples will be generated 1 / frame_rate seconds after __call__ is called.
            on_device_buffer (ndarray): The numpy array into which the noise samples will be written.
            buffer_lock (Lock): A threading lock created in the calling thread that will be used to ensure access to
                the on_device_buffer array is thread safe.

        """
        start_time = monotonic()
        while not stop_flag.is_set() and ((monotonic() - start_time) < (1 / frame_rate)):
            sleep(0.001)
        if not stop_flag.is_set():
            with buffer_lock:
                on_device_buffer[:] = randn(len(on_device_buffer))


class MultiFIFOModeMockWaveformSource(MockWaveformSource):
    def __call__(self, stop_flag: Event, frame_rate: float, on_device_buffer: ndarray, buffer_lock: Lock) -> None:
        """MultiFIFOModeMockWaveformSource

        When called, this MockWaveformSource simulates SPC_REC_FIFO_MULTI Mode, continuously replacing the contents
        of on_device_buffer with new frames of noise samples.

        Args:
            stop_flag (Event): A threading event that will be used in the calling thread to stop the acquisition.
            frame_rate (float): The contents of the on_device_buffer will be updated at this rate (Hz).
            on_device_buffer (ndarray): The numpy array into which the noise samples will be written.
            buffer_lock (Lock): A threading lock created in the calling thread that will be used to ensure access to
                the on_device_buffer array is thread safe.

        """
        while not stop_flag.is_set():
            with buffer_lock:
                on_device_buffer[:] = randn(len(on_device_buffer))
                sleep(1 / frame_rate)


def mock_waveform_source_factory(acquisition_mode: AcquisitionMode) -> MockWaveformSource:
    if acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
        return MultiFIFOModeMockWaveformSource()
    elif AcquisitionMode.SPC_REC_FIFO_SINGLE:
        return SingleModeMockWaveformSource()
    else:
        raise NotImplementedError("Mock waveform source not yet implemented for {acquisition_mode} acquisition mode.")
