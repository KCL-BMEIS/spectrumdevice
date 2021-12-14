from abc import ABC
from dataclasses import dataclass
from threading import Event, Lock, Thread
from time import sleep, monotonic
from typing import Optional, cast, Sequence, List

from numpy import ndarray, zeros
from numpy.random import randn

from pyspecde.hardware_model.spectrum_card import SpectrumCard
from pyspecde.hardware_model.spectrum_device import SpectrumDevice
from pyspecde.exceptions import SpectrumDeviceNotConnected
from pyspecde.hardware_model.spectrum_interface import SpectrumIntLengths
from pyspecde.spectrum_api_wrapper import DEVICE_HANDLE_TYPE, AcquisitionMode
from pyspecde.spectrum_api_wrapper.transfer_buffer import TransferBuffer, transfer_buffer_factory
from pyspecde.hardware_model.spectrum_star_hub import SpectrumStarHub
from tests.test_configuration import TEST_SPECTRUM_STAR_HUB_CONFIG, TEST_SPECTRUM_CARD_CONFIG
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
    SPCM_FEAT_EXTFW_SEGSTAT, SPC_TIMEOUT, SPC_SEGMENTSIZE, SPC_MEMSIZE, SPC_CHENABLE,
)
from pyspecde.spectrum_api_wrapper.mock_pyspcm import drv_handle


class MockSpectrumDevice(SpectrumDevice, ABC):
    def __init__(self) -> None:
        self._param_dict = {
            SPC_MIINST_MODULES: TEST_SPECTRUM_CARD_CONFIG.num_modules,
            SPC_MIINST_CHPERMODULE: TEST_SPECTRUM_CARD_CONFIG.num_channels_per_module,
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
        self._acquisition_stop_event = Event()
        self._acquisition_thread: Optional[Thread] = None
        self._on_device_buffer: ndarray = zeros(1)
        self._enabled_channels = [0]
        self._previous_data = self._on_device_buffer.copy()

    def start_acquisition(self) -> None:
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI or \
                self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_SINGLE:
            target = mock_fifo_mode_source
        else:
            target = mock_single_mode_source
        self._acquisition_stop_event.clear()
        self._acquisition_thread = Thread(target=target, args=(self._acquisition_stop_event, self._on_device_buffer,
                                                               self._buffer_lock))
        self._acquisition_thread.start()

    def stop_acquisition(self) -> None:
        print('Stopping acquisition')
        self._acquisition_stop_event.set()

    def set_spectrum_api_param(
        self, spectrum_command: int, value: int, length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO
    ) -> None:
        self._param_dict[spectrum_command] = value

    def get_spectrum_api_param(
        self, spectrum_command: int, length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO
    ) -> int:
        if spectrum_command in self._param_dict:
            return self._param_dict[spectrum_command]
        else:
            self._param_dict[spectrum_command] = -1
            return -1


class MockSpectrumCard(SpectrumCard, MockSpectrumDevice):
    def __init__(self):
        mock_handle = cast(DEVICE_HANDLE_TYPE, drv_handle)
        MockSpectrumDevice.__init__(self)
        SpectrumCard.__init__(self, mock_handle)

    def set_acquisition_length_samples(self, length_in_samples: int) -> None:
        self._on_device_buffer = zeros(self.acquisition_length_samples * len(self.enabled_channels))
        super().set_acquisition_length_samples(length_in_samples)

    def set_enabled_channels(self, channels_nums: List[int]) -> None:
        self._on_device_buffer = zeros(self.acquisition_length_samples * len(channels_nums))
        super().set_enabled_channels(channels_nums)

    def disconnect(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot disconnect mock card")

    def define_transfer_buffer(self, buffer: Optional[TransferBuffer] = None) -> None:
        if buffer:
            self._transfer_buffer = buffer
        else:
            self._transfer_buffer = transfer_buffer_factory(
                self.acquisition_length_samples * len(self.enabled_channels)
            )

    def start_transfer(self) -> None:
        self._transfer_buffer.data_buffer = self._on_device_buffer

    def stop_transfer(self) -> None:
        self._transfer_buffer.data_buffer = zeros(self._transfer_buffer.data_buffer.shape)

    def wait_for_transfer_to_complete(self) -> None:
        while (self._previous_data == self._transfer_buffer.data_buffer).all():
            sleep(0.01)
        self._previous_data = self._transfer_buffer.data_buffer.copy()

    def wait_for_acquisition_to_complete(self) -> None:
        self._acquisition_thread.join(timeout=1e-3 * self.timeout_ms)
        if self._acquisition_thread.is_alive():
            print("A timeout occurred while waiting for mock acquisition to complete.")


class MockSpectrumStarHub(SpectrumStarHub, MockSpectrumDevice):
    def __init__(self, hub_handle: DEVICE_HANDLE_TYPE, child_cards: Sequence[SpectrumCard], master_card_index: int):
        MockSpectrumDevice.__init__(self)
        SpectrumStarHub.__init__(self, hub_handle, child_cards, master_card_index)

    def disconnect(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot disconnect mock card")


def mock_single_mode_source(stop_flag: Event, on_device_buffer: ndarray, buffer_lock: Lock) -> None:
    start_time = monotonic()
    while not stop_flag.is_set() and ((monotonic() - start_time) < 0.1):
        sleep(0.01)
    if not stop_flag.is_set():
        with buffer_lock:
            on_device_buffer[:] = randn(len(on_device_buffer))


def mock_fifo_mode_source(stop_flag: Event, on_device_buffer: ndarray, buffer_lock: Lock) -> None:
    while not stop_flag.is_set():
        with buffer_lock:
            on_device_buffer[:] = randn(len(on_device_buffer))
            sleep(0.5)


def mock_spectrum_card_factory() -> MockSpectrumCard:
    return MockSpectrumCard()


def mock_spectrum_star_hub_factory() -> MockSpectrumStarHub:
    cards = [mock_spectrum_card_factory() for _ in range(TEST_SPECTRUM_STAR_HUB_CONFIG.num_cards)]
    mock_hub_handle = cast(DEVICE_HANDLE_TYPE, drv_handle)
    return MockSpectrumStarHub(mock_hub_handle, cards, 0)
