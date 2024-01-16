from unittest import TestCase

from spectrumdevice import MockSpectrumDigitiserCard
from spectrumdevice.exceptions import SpectrumFeatureNotSupportedByCard
from spectrumdevice.settings import ModelNumber
from spectrumdevice.settings.pulse_generator import PulseGeneratorTriggerDetectionMode, PulseGeneratorTriggerMode
from tests.configuration import (
    MOCK_DEVICE_TEST_FRAME_RATE_HZ,
    NUM_CHANNELS_PER_DIGITISER_MODULE,
    NUM_MODULES_PER_DIGITISER,
    TEST_DIGITISER_NUMBER,
)
from tests.device_factories import create_awg_card_for_testing


class PulseGeneratorTest(TestCase):
    def setUp(self) -> None:
        self._awg = create_awg_card_for_testing()

    def test_pulse_gen_feat_not_available(self) -> None:
        mock_digitiser_without_pulse_gen = MockSpectrumDigitiserCard(
            device_number=TEST_DIGITISER_NUMBER,
            model=ModelNumber.TYP_M2P5966_X4,
            mock_source_frame_rate_hz=MOCK_DEVICE_TEST_FRAME_RATE_HZ,
            num_modules=NUM_MODULES_PER_DIGITISER,
            num_channels_per_module=NUM_CHANNELS_PER_DIGITISER_MODULE,
            card_features=[],
            advanced_card_features=[],
        )
        with self.assertRaises(SpectrumFeatureNotSupportedByCard):
            _ = mock_digitiser_without_pulse_gen.io_lines[0].pulse_generator

    def test_get_pulse_gens(self) -> None:
        for io_line in self._awg.io_lines:
            _ = io_line.pulse_generator

    def test_enable_disable(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        self.assertFalse(pg.enabled)
        pg.enable()
        self.assertTrue(pg.enabled)
        pg.disable()
        self.assertFalse(pg.enabled)

    def test_output_inversion(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        self.assertFalse(pg.output_inversion)
        pg.set_output_inversion(True)
        self.assertTrue(pg.output_inversion)
        pg.set_output_inversion(False)
        self.assertFalse(pg.output_inversion)

    def test_trigger_detection_mode(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        self.assertEqual(PulseGeneratorTriggerDetectionMode.RISING_EDGE, pg.trigger_detection_mode)
        pg.set_trigger_detection_mode(PulseGeneratorTriggerDetectionMode.SPCM_PULSEGEN_CONFIG_HIGH)
        self.assertEqual(PulseGeneratorTriggerDetectionMode.SPCM_PULSEGEN_CONFIG_HIGH, pg.trigger_detection_mode)
        pg.set_trigger_detection_mode(PulseGeneratorTriggerDetectionMode.RISING_EDGE)
        self.assertEqual(PulseGeneratorTriggerDetectionMode.RISING_EDGE, pg.trigger_detection_mode)

    def test_trigger_mode(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_trigger_mode(PulseGeneratorTriggerMode.SPCM_PULSEGEN_MODE_TRIGGERED)
        self.assertEqual(PulseGeneratorTriggerMode.SPCM_PULSEGEN_MODE_TRIGGERED, pg.trigger_mode)
        pg.set_trigger_mode(PulseGeneratorTriggerMode.SPCM_PULSEGEN_MODE_GATED)
        self.assertEqual(PulseGeneratorTriggerMode.SPCM_PULSEGEN_MODE_GATED, pg.trigger_mode)

    def test_pulse_period(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_period_in_seconds(1)
        self.assertEqual(1, pg.period_in_seconds)

    def test_duty_cycle(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_period_in_seconds(1)
        pg.set_duty_cycle(0.5)
        self.assertEqual(0.5, pg.duty_cycle)

    def test_num_pulses(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_num_pulses(500)
        self.assertEqual(500, pg.num_pulses)

    def test_delay(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_delay_in_seconds(10)
        self.assertEqual(10, pg.delay_in_seconds)
