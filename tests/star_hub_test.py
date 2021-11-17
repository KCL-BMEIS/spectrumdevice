from numpy import zeros, array

from pyspecde.spectrum_device import SpectrumChannel
from pyspecde.sdk_translation_layer import SpectrumChannelName, TransferBuffer, BufferType, BufferDirection
from pyspecde.spectrum_star_hub import SpectrumStarHub
from tests.mock_spectrum_device import (
    mock_spectrum_star_hub_factory,
    NUM_CHANNELS_IN_MOCK_MODULE,
    NUM_MODULES_IN_MOCK_DEVICE,
    NUM_DEVICES_IN_MOCK_NETBOX,
)
from tests.single_card_test import SingleCardTest
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


class StarHubTest(SingleCardTest):
    def setUp(self) -> None:
        self._device: SpectrumStarHub = mock_spectrum_star_hub_factory()

    def test_count_channels(self) -> None:
        channels = self._device.channels
        expected_num_channels = NUM_CHANNELS_IN_MOCK_MODULE * NUM_MODULES_IN_MOCK_DEVICE * NUM_DEVICES_IN_MOCK_NETBOX
        self.assertEqual(len(channels), expected_num_channels)

    def test_channel_enabling(self) -> None:
        spectrum_command_to_enable_some_channels_dev_1 = CHANNEL0 | CHANNEL2 | CHANNEL4 | CHANNEL6
        spectrum_command_to_enable_some_channels_dev_2 = CHANNEL1 | CHANNEL3 | CHANNEL5 | CHANNEL7
        self._device.channels[1].set_enabled(False)
        self._device.channels[3].set_enabled(False)
        self._device.channels[5].set_enabled(False)
        self._device.channels[7].set_enabled(False)
        self._device.channels[8].set_enabled(False)
        self._device.channels[10].set_enabled(False)
        self._device.channels[12].set_enabled(False)
        self._device.channels[14].set_enabled(False)

        device_1_result = self._device.get_spectrum_api_param_all_cards(SPC_CHENABLE)[0]
        device_2_result = self._device.get_spectrum_api_param_all_cards(SPC_CHENABLE)[1]
        self.assertEqual(spectrum_command_to_enable_some_channels_dev_1, device_1_result)
        self.assertEqual(spectrum_command_to_enable_some_channels_dev_2, device_2_result)

    def test_get_channels(self) -> None:
        channels = self._device.channels
        expected_channels = [
            SpectrumChannel(SpectrumChannelName.CHANNEL0, self._device._child_cards[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL1, self._device._child_cards[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL2, self._device._child_cards[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL3, self._device._child_cards[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL4, self._device._child_cards[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL5, self._device._child_cards[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL6, self._device._child_cards[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL7, self._device._child_cards[0]),
            SpectrumChannel(SpectrumChannelName.CHANNEL0, self._device._child_cards[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL1, self._device._child_cards[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL2, self._device._child_cards[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL3, self._device._child_cards[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL4, self._device._child_cards[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL5, self._device._child_cards[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL6, self._device._child_cards[1]),
            SpectrumChannel(SpectrumChannelName.CHANNEL7, self._device._child_cards[1]),
        ]
        self.assertEqual(expected_channels, channels)

    def test_transfer_buffer(self) -> None:
        buffer = TransferBuffer(self._device.handle, BufferType.SPCM_BUF_DATA, BufferDirection.SPCM_DIR_CARDTOPC,
                                0, zeros(4096))
        self._device.set_transfer_buffer(buffer)
        with self.assertRaises(NotImplementedError):
            _ = self._device.transfer_buffer
        self.assertTrue((array(self._device.transfer_buffers) == buffer).all())
