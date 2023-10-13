import datetime
from typing import List
from unittest import TestCase

import pytest
from numpy import array, concatenate

from example_scripts.connect_to_star_hub import star_hub_example
from example_scripts.continuous_averaging_fifo_mode import continuous_averaging_multi_fifo_example
from example_scripts.continuous_multi_fifo_mode import continuous_multi_fifo_example
from example_scripts.finite_multi_fifo_mode import finite_multi_fifo_example
from example_scripts.standard_single_mode import standard_single_mode_example
from spectrumdevice.measurement import Measurement
from spectrumdevice.exceptions import SpectrumDriversNotFound
from tests.configuration import (
    ACQUISITION_LENGTH,
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
        measurement = standard_single_mode_example(
            mock_mode=self._single_card_mock_mode,
            trigger_source=INTEGRATION_TEST_TRIGGER_SOURCE,
            device_number=TEST_DEVICE_NUMBER,
            ip_address=TEST_DEVICE_IP,
            acquisition_length=ACQUISITION_LENGTH,
        )
        self.assertEqual(len(measurement.waveforms), 1)
        self.assertEqual([wfm.shape for wfm in measurement.waveforms], [(ACQUISITION_LENGTH,)])
        if self._single_card_mock_mode:
            self.assertAlmostEqual(measurement.waveforms[0].max() - measurement.waveforms[0].min(), 0.4, 1)
            self.assertAlmostEqual(measurement.waveforms[0].mean(), 0.0, 1)

        two_seconds_ago = datetime.datetime.now() - datetime.timedelta(seconds=2)
        now = datetime.datetime.now()
        if measurement.timestamp:
            self.assertTrue(two_seconds_ago < measurement.timestamp <= now)
        else:
            raise IOError("No timestamp available")

    def test_finite_multi_fifo_mode(self) -> None:
        measurements = finite_multi_fifo_example(
            mock_mode=self._single_card_mock_mode,
            num_measurements=5,
            batch_size=5,
            trigger_source=INTEGRATION_TEST_TRIGGER_SOURCE,
            device_number=TEST_DEVICE_NUMBER,
            ip_address=TEST_DEVICE_IP,
            acquisition_length=ACQUISITION_LENGTH,
        )
        self.assertEqual(len(measurements), 5)
        self._asserts_for_fifo_mode(measurements)

    def test_continuous_multi_fifo_mode(self) -> None:
        measurements = continuous_multi_fifo_example(
            mock_mode=self._single_card_mock_mode,
            time_to_keep_acquiring_for_in_seconds=0.5,
            batch_size=1,
            trigger_source=INTEGRATION_TEST_TRIGGER_SOURCE,
            device_number=TEST_DEVICE_NUMBER,
            ip_address=TEST_DEVICE_IP,
            single_acquisition_length_in_samples=ACQUISITION_LENGTH,
        )
        self._asserts_for_fifo_mode(measurements)

    def test_averaging_continuous_multi_fifo_example(self) -> None:
        measurements = continuous_averaging_multi_fifo_example(
            mock_mode=self._single_card_mock_mode,
            acquisition_duration_in_seconds=0.5,
            num_averages=2,
            trigger_source=INTEGRATION_TEST_TRIGGER_SOURCE,
            device_number=TEST_DEVICE_NUMBER,
            ip_address=TEST_DEVICE_IP,
            acquisition_length=ACQUISITION_LENGTH,
        )
        self._asserts_for_fifo_mode(measurements)

    def _asserts_for_fifo_mode(self, measurements: List[Measurement]) -> None:
        self.assertTrue((array([len(measurement.waveforms) for measurement in measurements]) == 1).all())

        waveforms = concatenate([measurement.waveforms for measurement in measurements])
        waveform_shapes = array([wfm.shape for wfm in waveforms])
        self.assertTrue((waveform_shapes == ACQUISITION_LENGTH).all())

        timestamps = array([measurement.timestamp for measurement in measurements])
        # Check timestamps all occurred within last second
        two_seconds_ago = datetime.datetime.now() - datetime.timedelta(seconds=2)
        self.assertTrue((two_seconds_ago < timestamps).all() and (timestamps <= datetime.datetime.now()).all())


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
            ip_address=TEST_DEVICE_IP,
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
