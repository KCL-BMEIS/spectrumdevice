from typing import List
from unittest import TestCase

import pytest
from numpy import array

from example_scripts.connect_to_star_hub import star_hub_example
from example_scripts.continuous_multi_fifo_mode import continuous_multi_fifo_example
from example_scripts.finite_multi_fifo_mode import finite_multi_fifo_example
from example_scripts.standard_single_mode import standard_single_mode_example
from spectrumdevice.devices.waveform import Waveform
from spectrumdevice.exceptions import SpectrumDriversNotFound
from tests.configuration import (
    INTEGRATION_TEST_TRIGGER_SOURCE,
    NUM_CARDS_IN_STAR_HUB,
    NUM_CHANNELS_PER_MODULE,
    NUM_MODULES_PER_CARD,
    SINGLE_CARD_TEST_MODE,
    STAR_HUB_MASTER_CARD_INDEX,
    STAR_HUB_TEST_MODE,
    SpectrumTestMode,
    TEST_DEVICE_IP,
    TEST_DEVICE_NUMBER,
)


@pytest.mark.integration
class SingleCardIntegrationTests(TestCase):
    def setUp(self) -> None:
        self._single_card_mock_mode = SINGLE_CARD_TEST_MODE == SpectrumTestMode.MOCK_HARDWARE

    def test_standard_single_mode(self) -> None:
        waveforms = standard_single_mode_example(
            mock_mode=self._single_card_mock_mode,
            trigger_source=INTEGRATION_TEST_TRIGGER_SOURCE,
            device_number=TEST_DEVICE_NUMBER,
            ip_address=TEST_DEVICE_IP,
        )
        self.assertEqual(len(waveforms), 1)
        self.assertEqual([wfm.samples.shape for wfm in waveforms], [(400,)])
        if self._single_card_mock_mode:
            self.assertAlmostEqual(waveforms[0].samples.max() - waveforms[0].samples.min(), 0.4, 1)
            self.assertAlmostEqual(waveforms[0].samples.mean(), 0.0, 1)

    def test_finite_multi_fifo_mode(self) -> None:
        measurements = finite_multi_fifo_example(
            mock_mode=self._single_card_mock_mode,
            num_measurements=5,
            trigger_source=INTEGRATION_TEST_TRIGGER_SOURCE,
            device_number=TEST_DEVICE_NUMBER,
            ip_address=TEST_DEVICE_IP,
        )
        self._asserts_for_fifo_mode(measurements)

    def test_continuous_multi_fifo_mode(self) -> None:
        measurements = continuous_multi_fifo_example(
            mock_mode=self._single_card_mock_mode,
            acquisition_duration_in_seconds=1.0,
            trigger_source=INTEGRATION_TEST_TRIGGER_SOURCE,
            device_number=TEST_DEVICE_NUMBER,
            ip_address=TEST_DEVICE_IP,
        )
        self._asserts_for_fifo_mode(measurements)

    def _asserts_for_fifo_mode(self, measurements: List[List[Waveform]]) -> None:
        self.assertTrue((array([len(measurement) for measurement in measurements]) == 1).all())
        self.assertTrue(
            (array([[wfm.samples.shape for wfm in waveforms] for waveforms in measurements]).flatten() == 400).all()
        )


@pytest.mark.integration
@pytest.mark.star_hub
class StarHubIntegrationTests(TestCase):
    def setUp(self) -> None:
        self._star_hub_mock_mode = STAR_HUB_TEST_MODE == SpectrumTestMode.MOCK_HARDWARE

    def test_star_hub(self) -> None:
        hub = star_hub_example(
            mock_mode=self._star_hub_mock_mode,
            num_cards=NUM_CARDS_IN_STAR_HUB,
            master_card_index=STAR_HUB_MASTER_CARD_INDEX,
        )
        self.assertEqual(len(hub.channels), NUM_CHANNELS_PER_MODULE * NUM_MODULES_PER_CARD * NUM_CARDS_IN_STAR_HUB)
        self.assertEqual(len(hub._child_cards), NUM_CARDS_IN_STAR_HUB)


@pytest.mark.integration
@pytest.mark.only_without_driver
class NoDriversTest(TestCase):
    def test_fails_with_no_driver_without_mock_mode(self) -> None:
        with self.assertRaises(SpectrumDriversNotFound):
            standard_single_mode_example(
                mock_mode=False, trigger_source=INTEGRATION_TEST_TRIGGER_SOURCE, device_number=TEST_DEVICE_NUMBER
            )
