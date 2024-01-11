from unittest import TestCase

from numpy import iinfo, int16

from spectrumdevice import SpectrumDigitiserAnalogChannel
from spectrumdevice.devices.awg.awg_channel import SpectrumAWGAnalogChannel
from spectrumdevice.settings import InputImpedance
from spectrumdevice.settings.channel import OutputChannelFilter, OutputChannelStopLevelMode
from tests.device_factories import create_awg_card_for_testing, create_digitiser_card_for_testing


class SingleDigitiserAnalogChannelTest(TestCase):
    def setUp(self) -> None:
        self._device = create_digitiser_card_for_testing()
        self._channel = SpectrumDigitiserAnalogChannel(channel_number=0, parent_device=self._device)

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

    def test_input_impedance(self) -> None:
        impedance = InputImpedance.ONE_MEGA_OHM
        self._channel.set_input_impedance(impedance)
        self.assertEqual(impedance, self._channel.input_impedance)


class SingleAWGAnalogChannelTest(TestCase):
    def setUp(self) -> None:
        self._device = create_awg_card_for_testing()
        self._channel = SpectrumAWGAnalogChannel(channel_number=0, parent_device=self._device)

    def test_switched_on(self) -> None:
        self._channel.set_is_switched_on(True)
        self.assertTrue(self._channel.is_switched_on)

    def test_dc_offset(self) -> None:
        self._channel.set_dc_offset_in_mv(100)
        self.assertEqual(100, self._channel.dc_offset_in_mv)

    def test_signal_amplitude(self) -> None:
        self._channel.set_signal_amplitude_in_mv(1000)
        self.assertEqual(1000, self._channel.signal_amplitude_in_mv)

    def test_output_filter(self) -> None:
        self._channel.set_output_filter(OutputChannelFilter.LOW_PASS_1_MHZ)
        self.assertEqual(OutputChannelFilter.LOW_PASS_1_MHZ, self._channel.output_filter)

    def test_stop_level_mode(self) -> None:
        self._channel.set_stop_level_mode(OutputChannelStopLevelMode.SPCM_STOPLVL_HIGH)
        self.assertEqual(OutputChannelStopLevelMode.SPCM_STOPLVL_HIGH, self._channel.stop_level_mode)

    def test_stop_level_custom_value(self) -> None:
        max_value = int16(iinfo(int16).max)
        self._channel.set_stop_level_custom_value(max_value)
        self.assertEqual(max_value, self._channel.stop_level_custom_value)
