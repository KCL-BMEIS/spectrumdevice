from numpy import zeros, array

from pyspecde.hardware_model.spectrum_channel import SpectrumChannel
from pyspecde.spectrum_api_wrapper.channel import SpectrumChannelName
from pyspecde.spectrum_api_wrapper.transfer_buffer import BufferType, BufferDirection, TransferBuffer
from pyspecde.hardware_model.spectrum_star_hub import SpectrumStarHub, spectrum_star_hub_factory
from pyspecde.exceptions import SpectrumDeviceNotConnected, SpectrumInvalidNumberOfEnabledChannels
from pyspecde.hardware_model.mock_spectrum_hardware import mock_spectrum_star_hub_factory
from tests.single_card_test import SingleCardTest
from tests.test_configuration import TEST_SPECTRUM_STAR_HUB_CONFIG, STAR_HUB_TEST_MODE, SpectrumTestMode
from spectrum_gmbh.regs import SPC_CHENABLE, SPC_SYNC_ENABLEMASK


class StarHubTest(SingleCardTest):
    def setUp(self) -> None:
        self._MOCK_MODE = STAR_HUB_TEST_MODE == SpectrumTestMode.MOCK_HARDWARE
        if self._MOCK_MODE:
            self._device: SpectrumStarHub = mock_spectrum_star_hub_factory()
        else:
            self._device = spectrum_star_hub_factory(
                TEST_SPECTRUM_STAR_HUB_CONFIG.ip_address,
                TEST_SPECTRUM_STAR_HUB_CONFIG.num_cards,
                TEST_SPECTRUM_STAR_HUB_CONFIG.master_card_index,
            )

        self._expected_num_channels = array(
            [card.num_channels for card in TEST_SPECTRUM_STAR_HUB_CONFIG.card_configs]
        ).sum()

        self._all_spectrum_channel_identifiers = [c.value for c in SpectrumChannelName]
        self._all_spectrum_channel_identifiers.sort()  # Enums are unordered so ensure channels are in ascending order

    def tearDown(self) -> None:
        if not self._MOCK_MODE:
            self._device.disconnect()

    def test_init(self) -> None:
        hub = mock_spectrum_star_hub_factory()
        self.assertEqual(3, hub.get_spectrum_api_param(SPC_SYNC_ENABLEMASK))

    def test_count_channels(self) -> None:
        channels = self._device.channels
        self.assertEqual(len(channels), self._expected_num_channels)

    def test_enable_one_channel(self) -> None:
        with self.assertRaises(SpectrumInvalidNumberOfEnabledChannels):
            self._device.set_enabled_channels([0])

    def test_enable_two_channels(self) -> None:

        channels_each_card = [card.num_channels for card in TEST_SPECTRUM_STAR_HUB_CONFIG.card_configs]
        num_channels_card_0 = channels_each_card[0]

        self._device.set_enabled_channels([0, num_channels_card_0])
        card_one_expected_command = self._all_spectrum_channel_identifiers[0]
        card_two_expected_command = self._all_spectrum_channel_identifiers[0]
        self.assertEqual(card_one_expected_command, self._device._child_cards[0].get_spectrum_api_param(SPC_CHENABLE))
        self.assertEqual(card_two_expected_command, self._device._child_cards[0].get_spectrum_api_param(SPC_CHENABLE))

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
        self._device.define_transfer_buffer(buffer)
        self.assertTrue((array(self._device.transfer_buffers) == buffer).all())

    def test_acquisition(self) -> None:
        if self._MOCK_MODE:
            with self.assertRaises(SpectrumDeviceNotConnected):
                self._device.start_acquisition()
        else:
            first_channel_each_card = [0] + [
                len(self._device._child_cards[n + 1].channels) for n in range(len(self._device._child_cards) - 1)
            ]
            window_length_samples = 16384
            acquisition_timeout_ms = 1000
            self._device.set_enabled_channels(first_channel_each_card)
            self._simple_acquisition(window_length_samples, acquisition_timeout_ms)
            acquired_waveforms = self._device.get_waveforms()
            self.assertEqual(len(acquired_waveforms), len(first_channel_each_card))
            waveform_lengths = array([len(wfm) for wfm in acquired_waveforms])
            self.assertTrue((waveform_lengths == window_length_samples).all())
            waveform_sums = array([wfm.sum() for wfm in acquired_waveforms])
            self.assertTrue((waveform_sums != 0.0).all())
