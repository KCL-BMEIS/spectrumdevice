from abc import ABC
from typing import cast, Sequence

from pyspecde.hardware_model.spectrum_card import SpectrumCard
from pyspecde.hardware_model.spectrum_device import SpectrumDevice
from pyspecde.spectrum_exceptions import SpectrumDeviceNotConnected
from pyspecde.hardware_model.spectrum_interface import SpectrumIntLengths
from pyspecde.sdk_translation_layer import DEVICE_HANDLE_TYPE, TransferBuffer
from pyspecde.hardware_model.spectrum_star_hub import SpectrumStarHub
from third_party.specde.py_header.regs import SPC_MIINST_MODULES, SPC_MIINST_CHPERMODULE
from tests.mock_pyspcm import drv_handle

NUM_CHANNELS_IN_MOCK_MODULE = 4
NUM_MODULES_IN_MOCK_CARD = 2
NUM_DEVICES_IN_MOCK_STAR_HUB = 2


class MockSpectrumDevice(SpectrumDevice, ABC):
    def __init__(self) -> None:
        self._param_dict = {
            SPC_MIINST_MODULES: NUM_MODULES_IN_MOCK_CARD,
            SPC_MIINST_CHPERMODULE: NUM_CHANNELS_IN_MOCK_MODULE,
        }

    def run(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot run mock device")

    def stop(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot stop mock device")

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

    def start_dma(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot start dma on mock device")

    def stop_dma(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot stop dma on mock device")

    def set_transfer_buffer(self, buffer: TransferBuffer) -> None:
        self._transfer_buffer = buffer


class MockSpectrumStarHub(SpectrumStarHub, MockSpectrumDevice):
    def __init__(self, hub_handle: DEVICE_HANDLE_TYPE, child_cards: Sequence[SpectrumCard], master_card_index: int):
        MockSpectrumDevice.__init__(self)
        SpectrumStarHub.__init__(self, hub_handle, child_cards, master_card_index)

    @property
    def transfer_buffer(self) -> TransferBuffer:
        raise NotImplementedError(
            "StarHubs create one transfer buffer per device. Access them using the " ".transfer_buffers property."
        )


def mock_spectrum_card_factory() -> MockSpectrumCard:
    mock_handle = cast(DEVICE_HANDLE_TYPE, drv_handle)
    return MockSpectrumCard(mock_handle)


def mock_spectrum_star_hub_factory() -> MockSpectrumStarHub:
    cards = [mock_spectrum_card_factory() for _ in range(NUM_DEVICES_IN_MOCK_STAR_HUB)]
    mock_hub_handle = cast(DEVICE_HANDLE_TYPE, drv_handle)
    return MockSpectrumStarHub(mock_hub_handle, cards, 0)
