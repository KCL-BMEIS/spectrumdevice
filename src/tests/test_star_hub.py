import pytest
from numpy import array

from spectrum_gmbh.regs import SPC_CHENABLE
from spectrumdevice import SpectrumDigitiserAnalogChannel, SpectrumDigitiserStarHub
from spectrumdevice.exceptions import SpectrumInvalidNumberOfEnabledChannels
from spectrumdevice.settings.channel import SpectrumAnalogChannelName
from spectrumdevice.settings.transfer_buffer import create_samples_acquisition_transfer_buffer
from tests.configuration import (
    ACQUISITION_LENGTH,
    NUM_CARDS_IN_STAR_HUB,
    NUM_CHANNELS_PER_DIGITISER_MODULE,
    NUM_MODULES_PER_DIGITISER,
)
from tests.device_factories import create_spectrum_star_hub_for_testing
from tests.test_single_card import SingleCardTest


@pytest.mark.star_hub
class StarHubTest(SingleCardTest):
    def setUp(self) -> None:
        self._device: SpectrumDigitiserStarHub = create_spectrum_star_hub_for_testing()

        self._expected_num_channels_each_card = NUM_CHANNELS_PER_DIGITISER_MODULE * NUM_MODULES_PER_DIGITISER
        self._expected_total_num_channels = self._expected_num_channels_each_card * NUM_CARDS_IN_STAR_HUB

        self._all_spectrum_channel_identifiers = [c.value for c in SpectrumAnalogChannelName]
        self._all_spectrum_channel_identifiers.sort()  # Enums are unordered to ensure channels are in ascending order

    def tearDown(self) -> None:
        self._device.disconnect()

    def test_count_channels(self) -> None:
        channels = self._device.analog_channels
        self.assertEqual(len(channels), self._expected_total_num_channels)

    def test_enable_one_channel(self) -> None:
        with self.assertRaises(SpectrumInvalidNumberOfEnabledChannels):
            self._device.set_enabled_analog_channels([0])

    def test_enable_two_channels(self) -> None:

        self._device.set_enabled_analog_channels([0, self._expected_num_channels_each_card])
        card_one_expected_command = self._all_spectrum_channel_identifiers[0]
        card_two_expected_command = self._all_spectrum_channel_identifiers[0]
        self.assertEqual(
            card_one_expected_command, self._device._child_cards[0].read_spectrum_device_register(SPC_CHENABLE)
        )
        self.assertEqual(
            card_two_expected_command, self._device._child_cards[0].read_spectrum_device_register(SPC_CHENABLE)
        )

    def test_get_channels(self) -> None:
        channels = self._device.analog_channels

        expected_channels = []
        for n in range(NUM_CARDS_IN_STAR_HUB):
            expected_channels += [
                SpectrumDigitiserAnalogChannel(channel_number=i, parent_device=self._device._child_cards[n])
                for i in range(self._expected_num_channels_each_card)
            ]
        expected_channels_tuple = tuple(expected_channels)
        self.assertEqual(expected_channels_tuple, channels)

    def test_transfer_buffer(self) -> None:

        buffer = [
            create_samples_acquisition_transfer_buffer(
                size_in_samples=ACQUISITION_LENGTH, bytes_per_sample=self._device.bytes_per_sample
            )
            for _ in range(NUM_CARDS_IN_STAR_HUB)
        ]
        self._device.define_transfer_buffer(buffer)
        self.assertTrue((array(self._device.transfer_buffers) == buffer).all())

    def test_features(self) -> None:
        try:
            feature_list = self._device.feature_list
        except Exception as e:
            self.assertTrue(False, f"raised an exception {e}")
            feature_list = []
        self.assertEqual(len(feature_list), NUM_CARDS_IN_STAR_HUB)
