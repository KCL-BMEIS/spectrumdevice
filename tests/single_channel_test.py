from unittest import TestCase

from pyspecde.hardware_model.spectrum_channel import spectrum_channel_factory
from tests.mock_spectrum_hardware import mock_spectrum_card_factory


class SingleChannelTest(TestCase):
    def setUp(self) -> None:
        self._device = mock_spectrum_card_factory()
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
