from numpy import zeros, array

from pyspecde.hardware_model.spectrum_channel import SpectrumChannel
from pyspecde.sdk_translation_layer import (
    SpectrumChannelName,
    TransferBuffer,
    BufferType,
    BufferDirection,
    MOCK_SDK_MODE,
)
from pyspecde.hardware_model.spectrum_star_hub import SpectrumStarHub, spectrum_star_hub_factory
from tests.mock_spectrum_hardware import (
    mock_spectrum_star_hub_factory,
    NUM_CHANNELS_IN_MOCK_MODULE,
    NUM_MODULES_IN_MOCK_CARD,
    NUM_DEVICES_IN_MOCK_STAR_HUB,
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
    SPC_SYNC_ENABLEMASK,
)

# todo: move to a unit test configuration file
TEST_START_HUB_IP_ADDRESS = "192.168.0.11"
NUM_CARDS_IN_TEST_STAR_HUB = 2


class StarHubTest(SingleCardTest):
    def setUp(self) -> None:
        if MOCK_SDK_MODE:
            self._device: SpectrumStarHub = mock_spectrum_star_hub_factory()
        else:
            self._device = spectrum_star_hub_factory(TEST_START_HUB_IP_ADDRESS, NUM_CARDS_IN_TEST_STAR_HUB)

    def test_init(self) -> None:
        hub = mock_spectrum_star_hub_factory()
        self.assertEqual(3, hub.get_spectrum_api_param(SPC_SYNC_ENABLEMASK))

    def test_count_channels(self) -> None:
        channels = self._device.channels
        # todo: include case for real device
        expected_num_channels = NUM_CHANNELS_IN_MOCK_MODULE * NUM_MODULES_IN_MOCK_CARD * NUM_DEVICES_IN_MOCK_STAR_HUB
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
        # todo: include case for real device
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
        buffer = TransferBuffer(
            self._device.handle, BufferType.SPCM_BUF_DATA, BufferDirection.SPCM_DIR_CARDTOPC, 0, zeros(4096)
        )
        self._device.set_transfer_buffer(buffer)
        with self.assertRaises(NotImplementedError):
            _ = self._device.transfer_buffer
        self.assertTrue((array(self._device.transfer_buffers) == buffer).all())
