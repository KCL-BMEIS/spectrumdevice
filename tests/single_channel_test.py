from unittest import TestCase

from spectrumdevice.devices.spectrum_channel import SpectrumChannel
from tests.test_device_factories import create_spectrum_card_for_testing


class SingleChannelTest(TestCase):
    def setUp(self) -> None:
        self._device = create_spectrum_card_for_testing()
        self._channel = SpectrumChannel(0, self._device)

    def tearDown(self) -> None:
        self._channel._parent_device.disconnect()

    def test_vertical_range(self) -> None:
        v_range = 5000
        self._channel.set_vertical_range_in_mv(v_range)
        self.assertEqual(v_range, self._channel.vertical_range_in_mv)

    def test_vertical_offset(self) -> None:
        offset = 1
        self._channel.set_vertical_offset_in_percent(offset)
        self.assertEqual(offset, self._channel.vertical_offset_in_percent)
