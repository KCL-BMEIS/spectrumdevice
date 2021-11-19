from numpy import zeros, array

from pyspecde.hardware_model.spectrum_channel import SpectrumChannel
from pyspecde.sdk_translation_layer import SpectrumChannelName, TransferBuffer, BufferType, BufferDirection
from pyspecde.hardware_model.spectrum_star_hub import SpectrumStarHub, spectrum_star_hub_factory
from tests.mock_spectrum_hardware import mock_spectrum_star_hub_factory
from tests.single_card_test import SingleCardTest
from tests.test_configuration import TEST_SPECTRUM_STAR_HUB_CONFIG, STAR_HUB_TEST_MODE, SpectrumTestMode
from third_party.specde.py_header.regs import SPC_CHENABLE, SPC_SYNC_ENABLEMASK


class StarHubTest(SingleCardTest):
    def setUp(self) -> None:
        self._MOCK_MODE = STAR_HUB_TEST_MODE == SpectrumTestMode.MOCK_HARDWARE
        if self._MOCK_MODE:
            self._device: SpectrumStarHub = mock_spectrum_star_hub_factory()
        else:
            self._device = spectrum_star_hub_factory(
                TEST_SPECTRUM_STAR_HUB_CONFIG.ip_address, TEST_SPECTRUM_STAR_HUB_CONFIG.num_cards
            )

        self._expected_num_channels = array(
            [card.num_channels for card in TEST_SPECTRUM_STAR_HUB_CONFIG.card_configs]
        ).sum()

        self._all_spectrum_channel_identifiers = [c.value for c in SpectrumChannelName]
        self._all_spectrum_channel_identifiers.sort()  # Enums are unordered so ensure channels are in ascending order

    def test_init(self) -> None:
        hub = mock_spectrum_star_hub_factory()
        self.assertEqual(3, hub.get_spectrum_api_param(SPC_SYNC_ENABLEMASK))

    def test_count_channels(self) -> None:
        channels = self._device.channels
        self.assertEqual(len(channels), self._expected_num_channels)

    def test_channel_enabling(self) -> None:

        total_channel_count = 0
        star_hub_indices_of_channels_to_enable = []
        enable_channels_commands = []

        for card_config in TEST_SPECTRUM_STAR_HUB_CONFIG.card_configs:
            enable_channels_command, indices_of_channels_to_enable = self._get_randomly_enable_channels(card_config)
            enable_channels_commands.append(enable_channels_command)
            star_hub_indices_of_channels_to_enable += list(array(indices_of_channels_to_enable) + total_channel_count)
            total_channel_count += card_config.num_channels

        # Enable only selected channels
        for i, channel in enumerate(self._device.channels):
            if i in star_hub_indices_of_channels_to_enable:
                channel.set_enabled(True)
            else:
                channel.set_enabled(False)

        for result, expected_result in zip(
            self._device.get_spectrum_api_param_all_cards(SPC_CHENABLE), enable_channels_commands
        ):
            self.assertEqual(expected_result, result)

    def test_get_channels(self) -> None:
        channels = self._device.channels

        expected_channels = []
        for n, card_config in enumerate(TEST_SPECTRUM_STAR_HUB_CONFIG.card_configs):
            expected_channels += [
                SpectrumChannel(
                    SpectrumChannelName(self._all_spectrum_channel_identifiers[i]), self._device._child_cards[n]
                )
                for i in range(card_config.num_channels)
            ]
        self.assertEqual(expected_channels, channels)

    def test_transfer_buffer(self) -> None:
        buffer = TransferBuffer(BufferType.SPCM_BUF_DATA, BufferDirection.SPCM_DIR_CARDTOPC, 0, zeros(4096))
        self._device.set_transfer_buffer(buffer)
        with self.assertRaises(NotImplementedError):
            _ = self._device.transfer_buffer
        self.assertTrue((array(self._device.transfer_buffers) == buffer).all())
