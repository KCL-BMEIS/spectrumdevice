from unittest import TestCase

from pyspecde.hardware_model.spectrum_card import spectrum_card_factory, SpectrumCard
from pyspecde.hardware_model.spectrum_channel import spectrum_channel_factory
from pyspecde.hardware_model.spectrum_star_hub import create_visa_string_from_ip
from tests.mock_spectrum_hardware import mock_spectrum_card_factory
from tests.test_configuration import TEST_SPECTRUM_CARD_CONFIG, SINGLE_CARD_TEST_MODE, SpectrumTestMode


class SingleChannelTest(TestCase):
    def setUp(self) -> None:
        if SINGLE_CARD_TEST_MODE == SpectrumTestMode.MOCK_HARDWARE:
            self._device: SpectrumCard = mock_spectrum_card_factory()
        else:
            self._device = spectrum_card_factory(
                create_visa_string_from_ip(
                    TEST_SPECTRUM_CARD_CONFIG.ip_address, TEST_SPECTRUM_CARD_CONFIG.visa_device_num
                )
            )
        self._channel = spectrum_channel_factory(0, self._device)

    def tearDown(self) -> None:
        self._channel._parent_device.disconnect()

    def test_vertical_range(self) -> None:
        v_range = 5000
        self._channel.set_vertical_range_mv(v_range)
        self.assertEqual(v_range, self._channel.vertical_range_mv)

    def test_vertical_offset(self) -> None:
        offset = 1
        self._channel.set_vertical_offset_percent(offset)
        self.assertEqual(offset, self._channel.vertical_offset_percent)
