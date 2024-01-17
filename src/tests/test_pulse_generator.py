from unittest import TestCase

from spectrumdevice import MockSpectrumDigitiserCard
from spectrumdevice.exceptions import SpectrumFeatureNotSupportedByCard, SpectrumInvalidParameterValue
from spectrumdevice.settings import ModelNumber
from spectrumdevice.settings.pulse_generator import (
    PulseGeneratorMultiplexer1TriggerSource,
    PulseGeneratorMultiplexer2TriggerSource,
    PulseGeneratorOutputSettings,
    PulseGeneratorTriggerDetectionMode,
    PulseGeneratorTriggerMode,
    PulseGeneratorTriggerSettings,
)
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
        self._awg.set_sample_rate_in_hz(1000000)
        self._awg.analog_channels[0].set_is_switched_on(True)
        self._awg.analog_channels[0].set_signal_amplitude_in_mv(1000)

    def tearDown(self) -> None:
        self._awg.reset()
        self._awg.disconnect()

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
        pg.set_period_in_seconds(pg.min_allowed_period_in_seconds)
        self.assertEqual(pg.min_allowed_period_in_seconds, pg.period_in_seconds)

    def test_coerce_pulse_period(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_period_in_seconds(pg.max_allowed_period_in_seconds + 1, coerce=True)
        self.assertAlmostEqual(pg.max_allowed_period_in_seconds, pg.period_in_seconds, places=5)

    def test_invalid_pulse_period(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        with self.assertRaises(SpectrumInvalidParameterValue):
            pg.set_period_in_seconds(pg.max_allowed_period_in_seconds + 1)

    def test_duty_cycle(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_period_in_seconds(pg.max_allowed_period_in_seconds)
        duty_cycle = pg.min_allowed_high_voltage_duration_in_seconds / pg.period_in_seconds
        pg.set_duty_cycle(duty_cycle)
        self.assertAlmostEqual(duty_cycle, pg.duty_cycle, places=5)

    def test_coerce_duty_cycle(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_period_in_seconds(pg.max_allowed_period_in_seconds)
        pg.set_duty_cycle(1.1, coerce=True)
        self.assertAlmostEqual(
            pg.max_allowed_high_voltage_duration_in_seconds, pg.duration_of_high_voltage_in_seconds, places=5
        )

    def test_invalid_duty_cycle(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        with self.assertRaises(SpectrumInvalidParameterValue):
            pg.set_period_in_seconds(pg.max_allowed_period_in_seconds)
            pg.set_duty_cycle(1.1)

    def test_num_pulses(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_num_pulses(pg.min_allowed_pulses)
        self.assertEqual(pg.min_allowed_pulses, pg.num_pulses)

    def test_coerce_num_pulses(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_num_pulses(pg.max_allowed_pulses + 1, coerce=True)
        self.assertEqual(pg.max_allowed_pulses, pg.num_pulses)

    def test_invalid_num_pulses(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        with self.assertRaises(SpectrumInvalidParameterValue):
            pg.set_num_pulses(pg.max_allowed_pulses + 1)

    def test_delay(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_delay_in_seconds(pg.min_allowed_delay_in_seconds)
        self.assertEqual(pg.min_allowed_delay_in_seconds, pg.delay_in_seconds)

    def test_coerce_delay(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        pg.set_delay_in_seconds(pg.max_allowed_delay_in_seconds + 1, coerce=True)
        self.assertAlmostEqual(pg.max_allowed_delay_in_seconds, pg.delay_in_seconds, places=5)

    def test_invalid_delay(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        with self.assertRaises(SpectrumInvalidParameterValue):
            pg.set_delay_in_seconds(pg.max_allowed_delay_in_seconds + 1)

    def test_configure_trigger(self) -> None:
        trigger_settings = PulseGeneratorTriggerSettings(
            trigger_mode=PulseGeneratorTriggerMode.SPCM_PULSEGEN_MODE_TRIGGERED,
            trigger_detection_mode=PulseGeneratorTriggerDetectionMode.RISING_EDGE,
            multiplexer_1_source=PulseGeneratorMultiplexer1TriggerSource.SPCM_PULSEGEN_MUX1_SRC_UNUSED,
            multiplexer_1_output_inversion=False,
            multiplexer_2_source=PulseGeneratorMultiplexer2TriggerSource.SPCM_PULSEGEN_MUX2_SRC_SOFTWARE,
            multiplexer_2_output_inversion=False,
        )
        pg = self._awg.io_lines[0].pulse_generator
        pg.configure_trigger(trigger_settings)

        self.assertEqual(PulseGeneratorTriggerMode.SPCM_PULSEGEN_MODE_TRIGGERED, pg.trigger_mode)
        self.assertEqual(PulseGeneratorTriggerDetectionMode.RISING_EDGE, pg.trigger_detection_mode)
        self.assertEqual(
            PulseGeneratorMultiplexer1TriggerSource.SPCM_PULSEGEN_MUX1_SRC_UNUSED, pg.multiplexer_1.trigger_source
        )
        self.assertFalse(pg.multiplexer_1.output_inversion)
        self.assertEqual(
            PulseGeneratorMultiplexer2TriggerSource.SPCM_PULSEGEN_MUX2_SRC_SOFTWARE, pg.multiplexer_2.trigger_source
        )
        self.assertFalse(pg.multiplexer_2.output_inversion)

    def test_configure_output(self) -> None:
        pg = self._awg.io_lines[0].pulse_generator
        duty_cycle = pg.min_allowed_high_voltage_duration_in_seconds / pg.max_allowed_period_in_seconds
        output_settings = PulseGeneratorOutputSettings(
            period_in_seconds=pg.max_allowed_period_in_seconds,
            duty_cycle=duty_cycle,
            num_pulses=pg.max_allowed_pulses,
            delay_in_seconds=pg.max_allowed_delay_in_seconds,
            output_inversion=True,
        )
        pg.configure_output(output_settings, coerce=False)
        self.assertEqual(pg.max_allowed_period_in_seconds, pg.period_in_seconds)
        self.assertEqual(duty_cycle, pg.duty_cycle)
        self.assertEqual(pg.max_allowed_pulses, pg.num_pulses)
        self.assertEqual(pg.max_allowed_delay_in_seconds, pg.delay_in_seconds)
        self.assertTrue(pg.output_inversion)
