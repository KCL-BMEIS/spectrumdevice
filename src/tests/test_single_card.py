from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from unittest import TestCase

from numpy import array, iinfo, int16
from numpy.testing import assert_array_equal

from spectrum_gmbh.regs import SPC_CHENABLE
from spectrumdevice import SpectrumDigitiserAnalogChannel
from spectrumdevice.devices.abstract_device import SpectrumDeviceInterface
from spectrumdevice.devices.awg.awg_channel import SpectrumAWGAnalogChannel
from spectrumdevice.devices.awg.awg_interface import SpectrumAWGInterface
from spectrumdevice.devices.digitiser import SpectrumDigitiserInterface
from spectrumdevice.exceptions import (
    SpectrumDeviceNotConnected,
    SpectrumExternalTriggerNotEnabled,
    SpectrumTriggerOperationNotImplemented,
)
from spectrumdevice.settings.channel import SpectrumAnalogChannelName
from spectrumdevice.settings.device_modes import AcquisitionMode, ClockMode, GenerationMode
from spectrumdevice.settings.transfer_buffer import create_samples_acquisition_transfer_buffer
from spectrumdevice.settings.triggering import ExternalTriggerMode, TriggerSource
from tests.configuration import ACQUISITION_LENGTH, NUM_CHANNELS_PER_MODULE, NUM_MODULES_PER_CARD
from tests.device_factories import create_awg_card_for_testing, create_digitiser_card_for_testing


CardInterfaceVar = TypeVar("CardInterfaceVar", bound=SpectrumDeviceInterface)


class SingleCardTest(TestCase, Generic[CardInterfaceVar], ABC):
    __test__ = False

    def setUp(self) -> None:
        self._device: CardInterfaceVar = self._create_test_card()
        self._all_spectrum_channel_identifiers = [c.value for c in SpectrumAnalogChannelName]
        self._all_spectrum_channel_identifiers.sort()  # Enums are unordered so ensure channels are in ascending order
        self._expected_num_channels = NUM_CHANNELS_PER_MODULE * NUM_MODULES_PER_CARD

    @abstractmethod
    def _create_test_card(self) -> CardInterfaceVar:
        raise NotImplementedError

    def tearDown(self) -> None:
        self._device.disconnect()

    def test_count_channels(self) -> None:
        channels = self._device.analog_channels
        self.assertEqual(self._expected_num_channels, len(channels))

    def test_enable_one_channel(self) -> None:
        self._device.set_enabled_analog_channels([0])
        self.assertEqual(
            self._all_spectrum_channel_identifiers[0], self._device.read_spectrum_device_register(SPC_CHENABLE)
        )

    def test_enable_two_channels(self) -> None:
        self._device.set_enabled_analog_channels([0, 1])
        expected_command = self._all_spectrum_channel_identifiers[0] | self._all_spectrum_channel_identifiers[1]
        self.assertEqual(expected_command, self._device.read_spectrum_device_register(SPC_CHENABLE))

    def test_timeout(self) -> None:
        timeout = 1000
        self._device.set_timeout_in_ms(1000)
        self.assertEqual(timeout, self._device.timeout_in_ms)

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
            _ = self._device.external_trigger_level_in_mv
        level = 10
        with self.assertRaises(SpectrumExternalTriggerNotEnabled):
            self._device.set_external_trigger_level_in_mv(level)
        with self.assertRaises(SpectrumTriggerOperationNotImplemented):
            sources = [TriggerSource.SPC_TMASK_EXT3]
            self._device.set_trigger_sources(sources)
            self._device.set_external_trigger_level_in_mv(level)
        sources = [TriggerSource.SPC_TMASK_EXT0]
        self._device.set_trigger_sources(sources)
        self._device.set_external_trigger_level_in_mv(level)
        self.assertEqual(level, self._device.external_trigger_level_in_mv)

    def test_clock_mode(self) -> None:
        mode = ClockMode.SPC_CM_INTPLL
        self._device.set_clock_mode(mode)
        self.assertEqual(mode, self._device.clock_mode)

    def test_sample_rate(self) -> None:
        rate = 20000000
        self._device.set_sample_rate_in_hz(rate)
        self.assertEqual(rate, self._device.sample_rate_in_hz)

    def test_features(self) -> None:
        try:
            feature_list = self._device.feature_list
        except Exception as e:
            self.assertTrue(False, f"raised an exception {e}")
            feature_list = []
        self.assertEqual(len(feature_list), 1)

    def test_available_io_modes(self) -> None:
        try:
            _ = self._device.available_io_modes
        except Exception as e:
            self.assertTrue(False, f"raised an exception {e}")

    def test_transfer_buffer(self) -> None:
        buffer = create_samples_acquisition_transfer_buffer(
            size_in_samples=ACQUISITION_LENGTH, bytes_per_sample=self._device.bytes_per_sample
        )
        self._device.define_transfer_buffer([buffer])
        self.assertEqual(buffer, self._device.transfer_buffers[0])

    def test_disconnect(self) -> None:
        self._device.set_sample_rate_in_hz(1000000)
        self.assertTrue(self._device.sample_rate_in_hz == 1000000)
        self._device.disconnect()
        with self.assertRaises(SpectrumDeviceNotConnected):
            self._device.set_sample_rate_in_hz(1000000)
        self._device.reconnect()


class DigitiserCardTest(SingleCardTest[SpectrumDigitiserInterface]):
    __test__ = True

    def _create_test_card(self) -> SpectrumDigitiserInterface:
        return create_digitiser_card_for_testing()

    def test_get_channels(self) -> None:
        channels = self._device.analog_channels

        expected_channels = tuple(
            [
                SpectrumDigitiserAnalogChannel(channel_number=i, parent_device=self._device)
                for i in range(self._expected_num_channels)
            ]
        )
        self.assertEqual(expected_channels, channels)

    def test_acquisition_length(self) -> None:
        acquisition_length = ACQUISITION_LENGTH
        self._device.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
        self._device.set_acquisition_length_in_samples(acquisition_length)
        self.assertEqual(acquisition_length, self._device.acquisition_length_in_samples)

    def test_post_trigger_length(self) -> None:
        post_trigger_length = ACQUISITION_LENGTH
        self._device.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
        self._device.set_post_trigger_length_in_samples(post_trigger_length)
        self.assertEqual(post_trigger_length, self._device.post_trigger_length_in_samples)

    def test_acquisition_mode(self) -> None:
        acquisition_mode = AcquisitionMode.SPC_REC_STD_SINGLE
        self._device.set_acquisition_mode(acquisition_mode)
        self.assertEqual(acquisition_mode, self._device.acquisition_mode)


class AWGCardTest(SingleCardTest[SpectrumAWGInterface]):
    __test__ = True

    def _create_test_card(self) -> SpectrumAWGInterface:
        return create_awg_card_for_testing()

    def test_get_channels(self) -> None:
        channels = self._device.analog_channels

        expected_channels = tuple(
            [
                SpectrumAWGAnalogChannel(channel_number=i, parent_device=self._device)
                for i in range(self._expected_num_channels)
            ]
        )
        self.assertEqual(expected_channels, channels)

    def test_generation_mode(self) -> None:
        generation_mode = GenerationMode.SPC_REP_STD_SINGLE
        self._device.set_generation_mode(generation_mode)
        self.assertEqual(generation_mode, self._device.generation_mode)

    def test_num_loops(self) -> None:
        self._device.set_num_loops(5)
        self.assertEqual(5, self._device.num_loops)

    def test_transfer_waveform(self) -> None:
        wfm = (array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]) * iinfo(int16).max).astype(int16)
        self._device.transfer_waveform(wfm)
        transferred_wfm = self._device.transfer_buffers[0].data_array
        assert_array_equal(wfm, transferred_wfm)
