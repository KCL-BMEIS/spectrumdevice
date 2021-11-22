from functools import reduce
from operator import or_
from typing import Tuple, List
from unittest import TestCase

from numpy import zeros, arange
from numpy.random import randint, shuffle

from pyspecde.hardware_model.spectrum_card import spectrum_card_factory
from pyspecde.hardware_model.spectrum_channel import SpectrumChannel
from pyspecde.hardware_model.spectrum_star_hub import create_visa_string_from_ip
from pyspecde.spectrum_exceptions import (
    SpectrumDeviceNotConnected,
    SpectrumExternalTriggerNotEnabled,
    SpectrumTriggerOperationNotImplemented,
    SpectrumApiCallFailed,
)
from pyspecde.hardware_model.spectrum_interface import (
    SpectrumDeviceInterface,
)
from pyspecde.sdk_translation_layer import (
    AcquisitionMode,
    TriggerSource,
    ClockMode,
    SpectrumChannelName,
    TransferBuffer,
    BufferType,
    BufferDirection,
    ExternalTriggerMode,
)
from tests.mock_spectrum_hardware import mock_spectrum_card_factory
from tests.test_configuration import (
    TEST_SPECTRUM_CARD_CONFIG,
    SpectrumTestMode,
    SINGLE_CARD_TEST_MODE,
    SpectrumCardConfig,
)
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
        self._device.set_acquisition_length_samples(acquisition_length)
        self.assertEqual(acquisition_length, self._device.acquisition_length_samples)

    def test_post_trigger_length(self) -> None:
        post_trigger_length = 2048
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

    def test_run(self) -> None:
        if self._MOCK_MODE:
            with self.assertRaises(SpectrumDeviceNotConnected):
                self._device.start_acquisition()
        else:
            # todo: implement run test for real device
            raise NotImplementedError()

    def test_stop(self) -> None:
        if self._MOCK_MODE:
            with self.assertRaises(SpectrumDeviceNotConnected):
                self._device.stop_acquisition()
        else:
            # todo: imlement stop test for real device
            raise NotImplementedError()
