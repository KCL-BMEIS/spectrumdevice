from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from unittest import TestCase

from numpy import array, iinfo, int16, zeros
from numpy.testing import assert_array_equal

from spectrum_gmbh.regs import SPC_CHENABLE
from spectrumdevice import SpectrumDigitiserAnalogChannel
from spectrumdevice.devices.abstract_device.device_interface import SpectrumDeviceInterface
from spectrumdevice.devices.awg.awg_channel import SpectrumAWGAnalogChannel
from spectrumdevice.devices.awg.awg_interface import SpectrumAWGInterface
from spectrumdevice.devices.digitiser import SpectrumDigitiserInterface
from spectrumdevice.exceptions import (
    SpectrumDeviceNotConnected,
    SpectrumExternalTriggerNotEnabled,
    SpectrumTriggerOperationNotImplemented,
)
from spectrumdevice.settings import (
    AcquisitionSettings,
    InputImpedance,
    GenerationSettings,
    OutputChannelFilter,
    OutputChannelStopLevelMode,
)
from spectrumdevice.settings.channel import SpectrumAnalogChannelName
from spectrumdevice.settings.device_modes import AcquisitionMode, ClockMode, GenerationMode
from spectrumdevice.settings.transfer_buffer import (
    create_samples_acquisition_transfer_buffer,
    transfer_buffer_factory,
    BufferType,
    BufferDirection,
)
from spectrumdevice.settings.triggering import ExternalTriggerMode, TriggerSource
from tests.configuration import (
    ACQUISITION_LENGTH,
    NUM_CHANNELS_PER_DIGITISER_MODULE,
    NUM_MODULES_PER_DIGITISER,
    NUM_MODULES_PER_AWG,
    NUM_CHANNELS_PER_AWG_MODULE,
)
from tests.device_factories import create_awg_card_for_testing, create_digitiser_card_for_testing


CardInterfaceVar = TypeVar("CardInterfaceVar", bound=SpectrumDeviceInterface)


class SingleCardTest(TestCase, Generic[CardInterfaceVar], ABC):
    __test__ = False

    def setUp(self) -> None:
        self._device: CardInterfaceVar = self._create_test_card()
        self._all_spectrum_channel_identifiers = [c.value for c in SpectrumAnalogChannelName]
        self._all_spectrum_channel_identifiers.sort()  # Enums are unordered so ensure channels are in ascending order
        self._expected_num_channels = self._determine_expected_num_channels()

    @abstractmethod
    def _create_test_card(self) -> CardInterfaceVar:
        raise NotImplementedError

    @abstractmethod
    def _determine_expected_num_channels(self) -> int:
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
        if len(self._device.analog_channels) > 1:
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

    def _determine_expected_num_channels(self) -> int:
        return NUM_CHANNELS_PER_DIGITISER_MODULE * NUM_MODULES_PER_DIGITISER

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

    def test_transfer_buffer(self) -> None:
        buffer = create_samples_acquisition_transfer_buffer(
            size_in_samples=ACQUISITION_LENGTH, bytes_per_sample=self._device.bytes_per_sample
        )
        self._device.define_transfer_buffer([buffer])
        self.assertEqual(buffer, self._device.transfer_buffers[0])

    def test_configure_acquisition(self) -> None:
        channel_to_enable = 1
        acquisition_settings = AcquisitionSettings(
            acquisition_mode=AcquisitionMode.SPC_REC_STD_SINGLE,
            sample_rate_in_hz=int(4e6),
            acquisition_length_in_samples=400,
            pre_trigger_length_in_samples=0,
            timeout_in_ms=1000,
            enabled_channels=[channel_to_enable],  # enable only second channel
            vertical_ranges_in_mv=[1000],
            vertical_offsets_in_percent=[10],
            input_impedances=[InputImpedance.FIFTY_OHM],
            timestamping_enabled=False,
        )
        self._device.configure_acquisition(acquisition_settings)

        expected_posttrigger_len = (
            acquisition_settings.acquisition_length_in_samples - acquisition_settings.pre_trigger_length_in_samples
        )

        self.assertEqual(acquisition_settings.acquisition_mode, self._device.acquisition_mode)
        self.assertEqual(acquisition_settings.sample_rate_in_hz, self._device.sample_rate_in_hz)
        self.assertEqual(acquisition_settings.acquisition_length_in_samples, self._device.acquisition_length_in_samples)
        self.assertEqual(expected_posttrigger_len, self._device.post_trigger_length_in_samples)
        self.assertEqual(acquisition_settings.timeout_in_ms, self._device.timeout_in_ms)
        self.assertEqual(acquisition_settings.enabled_channels, self._device.enabled_analog_channel_nums)
        self.assertEqual(
            acquisition_settings.vertical_ranges_in_mv[0],
            self._device.analog_channels[channel_to_enable].vertical_range_in_mv,
        )
        self.assertEqual(
            acquisition_settings.vertical_offsets_in_percent[0],
            self._device.analog_channels[channel_to_enable].vertical_offset_in_percent,
        )
        self.assertEqual(acquisition_settings.input_impedances[0], self._device.analog_channels[1].input_impedance)


class AWGCardTest(SingleCardTest[SpectrumAWGInterface]):
    __test__ = True

    def _create_test_card(self) -> SpectrumAWGInterface:
        return create_awg_card_for_testing()

    def _determine_expected_num_channels(self) -> int:
        return NUM_CHANNELS_PER_AWG_MODULE * NUM_MODULES_PER_AWG

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
        wfm = (
            array([0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8])
            * iinfo(int16).max
        ).astype(int16)
        self._device.transfer_waveform(wfm)
        transferred_wfm = self._device.transfer_buffers[0].data_array
        assert_array_equal(wfm, transferred_wfm)

    def test_transfer_too_small_waveform(self) -> None:
        wfm = array([0.0])
        with self.assertRaises(ValueError):
            self._device.transfer_waveform(wfm)

    def test_transfer_buffer(self) -> None:
        buffer = transfer_buffer_factory(
            buffer_type=BufferType.SPCM_BUF_DATA,
            direction=BufferDirection.SPCM_DIR_PCTOCARD,
            size_in_samples=16,
            bytes_per_sample=self._device.bytes_per_sample,
        )
        self._device.define_transfer_buffer([buffer])
        self.assertEqual(buffer, self._device.transfer_buffers[0])

    def test_configure_generation(self) -> None:
        generation_settings = GenerationSettings(
            generation_mode=GenerationMode.SPC_REP_STD_SINGLERESTART,
            waveform=zeros(16, dtype=int16),
            sample_rate_in_hz=1000000,
            num_loops=1,
            enabled_channels=[0],
            signal_amplitudes_in_mv=[1000],
            dc_offsets_in_mv=[0],
            output_filters=[OutputChannelFilter.LOW_PASS_70_MHZ],
            stop_level_modes=[OutputChannelStopLevelMode.SPCM_STOPLVL_ZERO],
        )
        self._device.configure_generation(generation_settings)
        self.assertEqual(generation_settings.generation_mode, self._device.generation_mode)
        assert_array_equal(generation_settings.waveform, self._device.transfer_buffers[0].data_array)
        self.assertEqual(generation_settings.sample_rate_in_hz, self._device.sample_rate_in_hz)
        self.assertEqual(generation_settings.num_loops, self._device.num_loops)
        self.assertEqual(generation_settings.enabled_channels, self._device.enabled_analog_channel_nums)
        self.assertEqual(
            generation_settings.signal_amplitudes_in_mv[0], self._device.analog_channels[0].signal_amplitude_in_mv
        )
        self.assertEqual(generation_settings.dc_offsets_in_mv[0], self._device.analog_channels[0].dc_offset_in_mv)
        self.assertEqual(generation_settings.output_filters[0], self._device.analog_channels[0].output_filter)
        self.assertEqual(generation_settings.stop_level_modes[0], self._device.analog_channels[0].stop_level_mode)
