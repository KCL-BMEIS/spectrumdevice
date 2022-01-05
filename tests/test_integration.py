from typing import List
from unittest import TestCase

import pytest
from numpy import ndarray

from example_scripts.connect_to_star_hub import star_hub_example  # type: ignore
from example_scripts.continuous_multi_fifo_mode import continuous_multi_fifo_example  # type: ignore
from example_scripts.finite_multi_fifo_mode import finite_multi_fifo_example  # type: ignore
from example_scripts.standard_single_mode import standard_single_mode_example  # type: ignore
from spectrumdevice.exceptions import SpectrumDriversNotFound


@pytest.mark.integration
class StandardSingleModeTest(TestCase):
    def test_standard_single_mode(self) -> None:
        waveforms = standard_single_mode_example(mock_mode=True)
        self.assertEqual(len(waveforms), 4)
        self.assertEqual([wfm.shape for wfm in waveforms], [(400,), (400,), (400,), (400,)])

    def test_finite_multi_fifo_mode(self) -> None:
        measurements = finite_multi_fifo_example(mock_mode=True, num_measurements=2)
        self._asserts_for_fifo_mode(measurements)

    def test_continuous_multi_fifo_mode(self) -> None:
        measurements = continuous_multi_fifo_example(mock_mode=True, acquisition_duration_in_seconds=1.0)
        self._asserts_for_fifo_mode(measurements)

    def _asserts_for_fifo_mode(self, measurements: List[List[ndarray]]) -> None:
        self.assertEqual(len(measurements), 2)
        self.assertEqual([len(measurement) for measurement in measurements], [4, 4])
        self.assertEqual(
            [[wfm.shape for wfm in waveforms] for waveforms in measurements],
            [[(400,), (400,), (400,), (400,)], [(400,), (400,), (400,), (400,)]],
        )

    def test_star_hub(self) -> None:
        hub = star_hub_example(mock_mode=True, num_cards=2, master_card_index=1)
        self.assertEqual(len(hub.channels), 16)
        self.assertEqual(len(hub._child_cards), 2)

    def test_fails_with_no_driver_or_mock_mode(self) -> None:
        with self.assertRaises(SpectrumDriversNotFound):
            standard_single_mode_example(mock_mode=False)
