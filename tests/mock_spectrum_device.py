from typing import cast

from pyspecde.spectrum_device import SpectrumCard
from pyspecde.spectrum_exceptions import SpectrumDeviceNotConnected
from pyspecde.spectrum_interface import SpectrumIntLengths
from pyspecde.sdk_translation_layer import DEVICE_HANDLE_TYPE, TransferBuffer
from pyspecde.spectrum_star_hub import SpectrumStarHub
from third_party.specde.py_header.regs import SPC_MIINST_MODULES, SPC_MIINST_CHPERMODULE
from tests.mock_pyspcm import drv_handle

NUM_CHANNELS_IN_MOCK_MODULE = 4
NUM_MODULES_IN_MOCK_DEVICE = 2
NUM_DEVICES_IN_MOCK_NETBOX = 2


class MockSpectrumCard(SpectrumCard):
    def __init__(self, handle: DEVICE_HANDLE_TYPE):
        self._param_dict = {
            SPC_MIINST_MODULES: NUM_MODULES_IN_MOCK_DEVICE,
            SPC_MIINST_CHPERMODULE: NUM_CHANNELS_IN_MOCK_MODULE,
        }
        super().__init__(handle)

    def disconnect(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot disconnect mock device")

    def start_dma(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot start dma on mock device")

    def stop_dma(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot stop dma on mock device")

    def run(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot run mock device")

    def stop(self) -> None:
        raise SpectrumDeviceNotConnected("Cannot stop mock device")

    def set_transfer_buffer(self, buffer: TransferBuffer) -> None:
        self._transfer_buffer = buffer

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


def mock_spectrum_card_factory() -> MockSpectrumCard:
    mock_handle = cast(DEVICE_HANDLE_TYPE, drv_handle)
    return MockSpectrumCard(mock_handle)


def mock_spectrum_star_hub_factory() -> SpectrumStarHub:
    cards = [mock_spectrum_card_factory() for _ in range(NUM_DEVICES_IN_MOCK_NETBOX)]
    mock_hub_handle = cast(DEVICE_HANDLE_TYPE, drv_handle)
    return SpectrumStarHub(mock_hub_handle, cards, 0)
