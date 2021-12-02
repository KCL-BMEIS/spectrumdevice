from unittest import TestCase

from numpy import zeros

from pyspecde.hardware_model.spectrum_card import spectrum_card_factory
from pyspecde.hardware_model.spectrum_channel import SpectrumChannel
from pyspecde.hardware_model.spectrum_interface import (
    SpectrumDeviceInterface,
)
from pyspecde.hardware_model.spectrum_star_hub import create_visa_string_from_ip
from pyspecde.sdk_translation_layer import (
    AcquisitionMode,
    BufferDirection,
    BufferType,
    ClockMode,
    ExternalTriggerMode,
    SpectrumChannelName,
    TransferBuffer,
    TriggerSource,
    transfer_buffer_factory,
)
from pyspecde.spectrum_exceptions import (
    SpectrumDeviceNotConnected,
    SpectrumExternalTriggerNotEnabled,
    SpectrumTriggerOperationNotImplemented,
)
from tests.mock_spectrum_hardware import mock_spectrum_card_factory
from tests.test_configuration import SINGLE_CARD_TEST_MODE, SpectrumTestMode, TEST_SPECTRUM_CARD_CONFIG
from third_party.specde.py_header.regs import SPC_CHENABLE


class SingleCardTest(TestCase):
    def setUp(self) -> None:
        self._MOCK_MODE = SINGLE_CARD_TEST_MODE == SpectrumTestMode.MOCK_HARDWARE
        if self._MOCK_MODE:
            self._device: SpectrumDeviceInterface = mock_spectrum_card_factory()
        else:
            self._device = spectrum_card_factory(
                create_visa_string_from_ip(
                    TEST_SPECTRUM_CARD_CONFIG.ip_address, TEST_SPECTRUM_CARD_CONFIG.visa_device_num
                )
            )

        self._all_spectrum_channel_identifiers = [c.value for c in SpectrumChannelName]
        self._all_spectrum_channel_identifiers.sort()  # Enums are unordered so ensure channels are in ascending order

    def tearDown(self) -> None:
        if not self._MOCK_MODE:
            self._device.disconnect()

    def test_count_channels(self) -> None:
        channels = self._device.channels
        self.assertEqual(len(channels), TEST_SPECTRUM_CARD_CONFIG.num_channels)

    def test_get_channels(self) -> None:
        channels = self._device.channels

        expected_channels = [
            SpectrumChannel(SpectrumChannelName(self._all_spectrum_channel_identifiers[i]), self._device)
            for i in range(TEST_SPECTRUM_CARD_CONFIG.num_channels)
        ]
        self.assertEqual(expected_channels, channels)

    def test_enable_one_channel(self) -> None:
        self._device.set_enabled_channels([0])
        self.assertEqual(self._all_spectrum_channel_identifiers[0], self._device.get_spectrum_api_param(SPC_CHENABLE))

    def test_enable_two_channels(self) -> None:
        self._device.set_enabled_channels([0, 1])
        expected_command = self._all_spectrum_channel_identifiers[0] | self._all_spectrum_channel_identifiers[1]
        self.assertEqual(expected_command, self._device.get_spectrum_api_param(SPC_CHENABLE))

    def test_acquisition_length(self) -> None:
        acquisition_length = 4096
        self._device.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
        self._device.set_acquisition_length_samples(acquisition_length)
        self.assertEqual(acquisition_length, self._device.acquisition_length_samples)

    def test_post_trigger_length(self) -> None:
        post_trigger_length = 2048
        self._device.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
        self._device.set_post_trigger_length_samples(post_trigger_length)
        self.assertEqual(post_trigger_length, self._device.post_trigger_length_samples)

    def test_acquisition_mode(self) -> None:
        acquisition_mode = AcquisitionMode.SPC_REC_STD_SINGLE
        self._device.set_acquisition_mode(acquisition_mode)
        self.assertEqual(acquisition_mode, self._device.acquisition_mode)

    def test_timeout(self) -> None:
        timeout = 1000
        self._device.set_timeout_ms(1000)
        self.assertEqual(timeout, self._device.timeout_ms)

    def test_trigger_sources(self) -> None:
        sources = [TriggerSource.SPC_TMASK_EXT0]
        self._device.set_trigger_sources(sources)
        self.assertEqual(sources, self._device.trigger_sources)

    def test_external_trigger_mode(self) -> None:
        with self.assertRaises(SpectrumExternalTriggerNotEnabled):
            _ = self._device.external_trigger_mode
        mode = ExternalTriggerMode.SPC_TM_POS
        with self.assertRaises(SpectrumExternalTriggerNotEnabled):
            self._device.set_external_trigger_mode(mode)
        sources = [TriggerSource.SPC_TMASK_EXT3]
        self._device.set_trigger_sources(sources)
        self._device.set_external_trigger_mode(mode)
        self.assertEqual(mode, self._device.external_trigger_mode)

    def test_external_trigger_level(self) -> None:
        with self.assertRaises(SpectrumExternalTriggerNotEnabled):
            _ = self._device.external_trigger_level_mv
        level = 10
        with self.assertRaises(SpectrumExternalTriggerNotEnabled):
            self._device.set_external_trigger_level_mv(level)
        with self.assertRaises(SpectrumTriggerOperationNotImplemented):
            sources = [TriggerSource.SPC_TMASK_EXT3]
            self._device.set_trigger_sources(sources)
            self._device.set_external_trigger_level_mv(level)
        sources = [TriggerSource.SPC_TMASK_EXT0]
        self._device.set_trigger_sources(sources)
        self._device.set_external_trigger_level_mv(level)
        self.assertEqual(level, self._device.external_trigger_level_mv)

    def test_clock_mode(self) -> None:
        mode = ClockMode.SPC_CM_INTPLL
        self._device.set_clock_mode(mode)
        self.assertEqual(mode, self._device.clock_mode)

    def test_sample_rate(self) -> None:
        rate = 20000000
        self._device.set_sample_rate_hz(rate)
        self.assertEqual(rate, self._device.sample_rate_hz)

    def test_features(self) -> None:
        try:
            _, _ = self._device.feature_list
        except Exception as e:
            self.assertTrue(False, f"raised an exception {e}")

    def test_available_io_modes(self) -> None:
        try:
            _ = self._device.available_io_modes
        except Exception as e:
            self.assertTrue(False, f"raised an exception {e}")

    def test_transfer_buffer(self) -> None:
        buffer = TransferBuffer(BufferType.SPCM_BUF_DATA, BufferDirection.SPCM_DIR_CARDTOPC, 0, zeros(4096))
        self._device.set_transfer_buffer(buffer)
        self.assertEqual(buffer, self._device.transfer_buffer)

    def test_disconnect(self) -> None:
        if self._MOCK_MODE:
            with self.assertRaises(SpectrumDeviceNotConnected):
                self._device.disconnect()
        else:
            self._device.set_acquisition_length_samples(4096)
            self.assertTrue(self._device.acquisition_length_samples == 4096)
            self._device.disconnect()
            with self.assertRaises(SpectrumDeviceNotConnected):
                self._device.set_acquisition_length_samples(4096)
            self.setUp()

    def test_acquisition(self) -> None:
        if self._MOCK_MODE:
            with self.assertRaises(SpectrumDeviceNotConnected):
                self._device.start_acquisition()
        else:
            window_length_samples = 16384
            acquisition_timeout_ms = 1000
            self._device.set_enabled_channels([0])
            self._simple_acquisition(window_length_samples, acquisition_timeout_ms)
            acquired_waveform = self._device.transfer_buffer.data_buffer
            self.assertEqual(len(acquired_waveform), window_length_samples)
            self.assertTrue(acquired_waveform.sum() != 0.0)

    def _simple_acquisition(self, window_length_samples: int, acquisition_timeout_ms: int) -> None:
        self._device.set_trigger_sources([TriggerSource.SPC_TMASK_SOFTWARE])
        self._device.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
        self._device.set_acquisition_length_samples(window_length_samples)
        self._device.set_post_trigger_length_samples(window_length_samples)
        self._device.set_timeout_ms(acquisition_timeout_ms)
        self._device.start_acquisition()
        self._device.wait_for_acquisition_to_complete()
        transfer_buffer = transfer_buffer_factory(window_length_samples * len(self._device.enabled_channels))
        self._device.set_transfer_buffer(transfer_buffer)
        self._device.start_transfer()
        self._device.wait_for_transfer_to_complete()
