from abc import ABC
from typing import Optional, cast, Sequence

from pyspecde.hardware_model.spectrum_card import SpectrumCard
from pyspecde.hardware_model.spectrum_device import SpectrumDevice
from pyspecde.spectrum_exceptions import SpectrumDeviceNotConnected
from pyspecde.hardware_model.spectrum_interface import SpectrumIntLengths
from pyspecde.sdk_translation_layer import DEVICE_HANDLE_TYPE, TransferBuffer, transfer_buffer_factory
from pyspecde.hardware_model.spectrum_star_hub import SpectrumStarHub
from tests.test_configuration import TEST_SPECTRUM_STAR_HUB_CONFIG, TEST_SPECTRUM_CARD_CONFIG
from third_party.specde.py_header.regs import (
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
)
from tests.mock_pyspcm import drv_handle


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
        }

    def start_acquisition(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot run mock device")

    def stop_acquisition(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot stop mock device")

    def wait_for_acquisition_to_complete(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot run mock device")

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
    def __init__(self, handle: DEVICE_HANDLE_TYPE):
        MockSpectrumDevice.__init__(self)
        SpectrumCard.__init__(self, handle)

    def disconnect(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot disconnect mock card")

    def set_transfer_buffer(self, buffer: Optional[TransferBuffer] = None) -> None:
        if buffer:
            self._transfer_buffer = buffer
        else:
            self._transfer_buffer = transfer_buffer_factory(
                self.acquisition_length_samples * len(self.enabled_channels)
            )


class MockSpectrumStarHub(SpectrumStarHub, MockSpectrumDevice):
    def __init__(self, hub_handle: DEVICE_HANDLE_TYPE, child_cards: Sequence[SpectrumCard], master_card_index: int):
        MockSpectrumDevice.__init__(self)
        SpectrumStarHub.__init__(self, hub_handle, child_cards, master_card_index)

    def disconnect(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot disconnect mock card")

    def start_transfer(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot stop dma on mock device")

    def stop_transfer(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot stop dma on mock device")

    @property
    def transfer_buffer(self) -> TransferBuffer:
        raise NotImplementedError(
            "StarHubs create one transfer buffer per device. Access them using the " ".transfer_buffers property."
        )


def mock_spectrum_card_factory() -> MockSpectrumCard:
    mock_handle = cast(DEVICE_HANDLE_TYPE, drv_handle)
    return MockSpectrumCard(mock_handle)


def mock_spectrum_star_hub_factory() -> MockSpectrumStarHub:
    cards = [mock_spectrum_card_factory() for _ in range(TEST_SPECTRUM_STAR_HUB_CONFIG.num_cards)]
    mock_hub_handle = cast(DEVICE_HANDLE_TYPE, drv_handle)
    return MockSpectrumStarHub(mock_hub_handle, cards, 0)
