from typing import cast

from pyspecde.spectrum_device import SpectrumDevice, DEVICE_HANDLE_TYPE
from pyspecde.spectrum_exceptions import SpectrumDeviceNotConnected
from pyspecde.spectrum_interface import SpectrumIntLengths
from pyspecde.spectrum_netbox import SpectrumNetbox
from third_party.specde.py_header.regs import SPC_MIINST_MODULES, SPC_MIINST_CHPERMODULE
from tests.mock_pyspcm import drv_handle

NUM_CHANNELS_IN_MOCK_MODULE = 4
NUM_MODULES_IN_MOCK_DEVICE = 2
NUM_DEVICES_IN_MOCK_NETBOX = 2


class MockSpectrumDevice(SpectrumDevice):

    def __init__(self, handle: DEVICE_HANDLE_TYPE):
        self._param_dict = {SPC_MIINST_MODULES: NUM_MODULES_IN_MOCK_DEVICE,
                            SPC_MIINST_CHPERMODULE: NUM_CHANNELS_IN_MOCK_MODULE}
        super().__init__(handle)

    def disconnect(self) -> None:
        raise SpectrumDeviceNotConnected('Cannot disconnect mock device')

    def set_spectrum_api_param(self, spectrum_command: int, value: int,
                               length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO) -> None:
        self._param_dict[spectrum_command] = value

    def get_spectrum_api_param(self, spectrum_command: int,
                               length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO) -> int:
        if spectrum_command in self._param_dict:
            return self._param_dict[spectrum_command]
        else:
            self._param_dict[spectrum_command] = -1
            return -1


def mock_spectrum_device_factory() -> MockSpectrumDevice:
    mock_handle = cast(DEVICE_HANDLE_TYPE, drv_handle)
    return MockSpectrumDevice(mock_handle)


def mock_spectrum_netbox_factory() -> SpectrumNetbox:
    return SpectrumNetbox(devices=[mock_spectrum_device_factory() for _ in range(NUM_DEVICES_IN_MOCK_NETBOX)])
