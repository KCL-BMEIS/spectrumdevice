from unittest import TestCase

from spectrumdevice import MockSpectrumDigitiserCard
from spectrumdevice.exceptions import SpectrumFeatureNotSupportedByCard
from spectrumdevice.settings import ModelNumber
from tests.configuration import (
    MOCK_DEVICE_TEST_FRAME_RATE_HZ,
    NUM_CHANNELS_PER_DIGITISER_MODULE,
    NUM_MODULES_PER_DIGITISER,
    TEST_DIGITISER_NUMBER,
)
from tests.device_factories import create_awg_card_for_testing, create_digitiser_card_for_testing


class PulseGeneratorTest(TestCase):
    def setUp(self) -> None:
        self._digitiser = create_digitiser_card_for_testing()
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
