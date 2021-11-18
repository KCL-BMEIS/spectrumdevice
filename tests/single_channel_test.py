from unittest import TestCase

from pyspecde.hardware_model.spectrum_card import spectrum_card_factory, SpectrumCard
from pyspecde.hardware_model.spectrum_channel import spectrum_channel_factory
from pyspecde.hardware_model.spectrum_star_hub import create_visa_string_from_ip
from pyspecde.sdk_translation_layer import MOCK_SDK_MODE
from tests.mock_spectrum_hardware import mock_spectrum_card_factory

TEST_CARD_IP_ADDRESS = "192.168.0.11"
TEST_CARD_DEVICE_NUM = 0


class SingleChannelTest(TestCase):
    def setUp(self) -> None:
        if MOCK_SDK_MODE:
            self._device: SpectrumCard = mock_spectrum_card_factory()
        else:
            self._device = spectrum_card_factory(create_visa_string_from_ip(TEST_CARD_IP_ADDRESS, TEST_CARD_DEVICE_NUM))
        self._channel = spectrum_channel_factory(0, self._device)

    def test_enabled(self) -> None:
        self.assertTrue(self._channel.enabled)

    def test_vertical_range(self) -> None:
        v_range = 10
        self._channel.set_vertical_range_mv(v_range)
        self.assertEqual(v_range, self._channel.vertical_range_mv)

    def test_vertical_offset(self) -> None:
        offset = 1
        self._channel.set_vertical_offset_percent(offset)
        self.assertEqual(offset, self._channel.vertical_offset_percent)
