from unittest import TestCase

from pyspecde.spectrum_device import SpectrumChannel
from pyspecde.spectrum_exceptions import SpectrumDeviceNotConnected
from pyspecde.spectrum_interface import (
    SpectrumChannelName,
    AcquisitionMode,
    TriggerSource,
    ClockMode,
    SpectrumInterface,
)
from tests.mock_spectrum_device import (
    mock_spectrum_device_factory,
    NUM_CHANNELS_IN_MOCK_MODULE,
    NUM_MODULES_IN_MOCK_DEVICE,
)
from third_party.specde.py_header.regs import CHANNEL0, CHANNEL2, CHANNEL4, CHANNEL6, SPC_CHENABLE


class SingleDeviceTest(TestCase):
    def setUp(self) -> None:
        self._device: SpectrumInterface = mock_spectrum_device_factory()

    def test_count_channels(self) -> None:
        channels = self._device.channels
        expected_num_channels = NUM_CHANNELS_IN_MOCK_MODULE * NUM_MODULES_IN_MOCK_DEVICE
        self.assertEqual(len(channels), expected_num_channels)

    def test_get_channels(self) -> None:
        channels = self._device.channels
        expected_channels = [
            SpectrumChannel(SpectrumChannelName.CHANNEL0, self._device),
            SpectrumChannel(SpectrumChannelName.CHANNEL1, self._device),
            SpectrumChannel(SpectrumChannelName.CHANNEL2, self._device),
            SpectrumChannel(SpectrumChannelName.CHANNEL3, self._device),
            SpectrumChannel(SpectrumChannelName.CHANNEL4, self._device),
            SpectrumChannel(SpectrumChannelName.CHANNEL5, self._device),
            SpectrumChannel(SpectrumChannelName.CHANNEL6, self._device),
            SpectrumChannel(SpectrumChannelName.CHANNEL7, self._device),
        ]
        self.assertEqual(expected_channels, channels)

    def test_channel_enabling(self) -> None:
        spectrum_command_to_enable_some_channels = CHANNEL0 | CHANNEL2 | CHANNEL4 | CHANNEL6
        self._device.channels[1].enabled = False
        self._device.channels[3].enabled = False
        self._device.channels[5].enabled = False
        self._device.channels[7].enabled = False
        self.assertEqual(spectrum_command_to_enable_some_channels, self._device.get_spectrum_api_param(SPC_CHENABLE))

    def test_acquisition_length(self) -> None:
        acquisition_length = 4096
        self._device.acquisition_length_bytes = acquisition_length
        self.assertEqual(acquisition_length, self._device.acquisition_length_bytes)

    def test_post_trigger_length(self) -> None:
        post_trigger_length = 2048
        self._device.post_trigger_length_bytes = post_trigger_length
        self.assertEqual(post_trigger_length, self._device.post_trigger_length_bytes)

    def test_acquisition_mode(self) -> None:
        acquisition_mode = AcquisitionMode.SPC_REC_STD_SINGLE
        self._device.acquisition_mode = acquisition_mode
        self.assertEqual(acquisition_mode, self._device.acquisition_mode)

    def test_timeout(self) -> None:
        timeout = 1000
        self._device.timeout_ms = 1000
        self.assertEqual(timeout, self._device.timeout_ms)

    def test_trigger_sources(self) -> None:
        sources = [TriggerSource.SPC_TMASK_EXT0]
        self._device.trigger_sources = sources
        self.assertEqual(sources, self._device.trigger_sources)

    def test_clock_mode(self) -> None:
        mode = ClockMode.SPC_CM_INTPLL
        self._device.clock_mode = mode
        self.assertEqual(mode, self._device.clock_mode)

    def test_sample_rate(self) -> None:
        rate = 3000000
        self._device.sample_rate_hz = rate
        self.assertEqual(rate, self._device.sample_rate_hz)

    def test_disconnect(self) -> None:
        with self.assertRaises(SpectrumDeviceNotConnected):
            self._device.disconnect()
