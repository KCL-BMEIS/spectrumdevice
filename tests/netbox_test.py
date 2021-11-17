from pyspecde.spectrum_device import SpectrumChannel
from pyspecde.spectrum_interface import SpectrumChannelName
from pyspecde.spectrum_netbox import SpectrumNetbox
from tests.mock_spectrum_device import (
    mock_spectrum_netbox_factory,
    NUM_CHANNELS_IN_MOCK_MODULE,
    NUM_MODULES_IN_MOCK_DEVICE,
    NUM_DEVICES_IN_MOCK_NETBOX,
)
from tests.single_device_test import SingleDeviceTest
from third_party.specde.py_header.regs import (
    CHANNEL0,
    CHANNEL3,
    CHANNEL6,
    CHANNEL2,
    CHANNEL4,
    SPC_CHENABLE,
    CHANNEL1,
    CHANNEL5,
    CHANNEL7,
)


class NetboxTest(SingleDeviceTest):
    def setUp(self) -> None:
        self._device: SpectrumNetbox = mock_spectrum_netbox_factory()

    def test_count_channels(self) -> None:
        channels = self._device.channels
        expected_num_channels = NUM_CHANNELS_IN_MOCK_MODULE * NUM_MODULES_IN_MOCK_DEVICE * NUM_DEVICES_IN_MOCK_NETBOX
        self.assertEqual(len(channels), expected_num_channels)

    def test_channel_enabling(self) -> None:
        spectrum_command_to_enable_some_channels_dev_1 = CHANNEL0 | CHANNEL2 | CHANNEL4 | CHANNEL6
        spectrum_command_to_enable_some_channels_dev_2 = CHANNEL1 | CHANNEL3 | CHANNEL5 | CHANNEL7
        self._device.channels[1].enabled = False
        self._device.channels[3].enabled = False
        self._device.channels[5].enabled = False
        self._device.channels[7].enabled = False
        self._device.channels[8].enabled = False
        self._device.channels[10].enabled = False
        self._device.channels[12].enabled = False
        self._device.channels[14].enabled = False

        device_1_result = self._device.get_spectrum_api_param_all_devices(SPC_CHENABLE)[0]
        device_2_result = self._device.get_spectrum_api_param_all_devices(SPC_CHENABLE)[1]
        self.assertEqual(spectrum_command_to_enable_some_channels_dev_1, device_1_result)
        self.assertEqual(spectrum_command_to_enable_some_channels_dev_2, device_2_result)

    def test_get_channels(self) -> None:
        channels = self._device.channels
        expected_channels = [
            SpectrumChannel(SpectrumChannelName.CHANNEL0, self._device._devices[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL1, self._device._devices[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL2, self._device._devices[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL3, self._device._devices[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL4, self._device._devices[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL5, self._device._devices[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL6, self._device._devices[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL7, self._device._devices[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL0, self._device._devices[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL1, self._device._devices[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL2, self._device._devices[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL3, self._device._devices[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL4, self._device._devices[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL5, self._device._devices[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL6, self._device._devices[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL7, self._device._devices[1]),
        ]
        self.assertEqual(expected_channels, channels)
