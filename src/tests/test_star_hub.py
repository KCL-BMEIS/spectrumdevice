import pytest
from numpy import array

from spectrum_gmbh.py_header.regs import SPC_CHENABLE
from spectrumdevice import SpectrumDigitiserAnalogChannel, SpectrumDigitiserStarHub
from spectrumdevice.exceptions import SpectrumInvalidNumberOfEnabledChannels
from spectrumdevice.settings import AcquisitionSettings, InputImpedance, AcquisitionMode
from spectrumdevice.settings.channel import SpectrumAnalogChannelName
from spectrumdevice.settings.transfer_buffer import create_samples_acquisition_transfer_buffer
from tests.configuration import (
    ACQUISITION_LENGTH,
    NUM_CARDS_IN_STAR_HUB,
    NUM_CHANNELS_PER_DIGITISER_MODULE,
    NUM_MODULES_PER_DIGITISER,
)
from tests.device_factories import create_spectrum_star_hub_for_testing
from tests.test_single_card import DigitiserCardTest


@pytest.mark.star_hub
class StarHubTest(DigitiserCardTest):
    __test__ = True

    def setUp(self) -> None:
        self._device: SpectrumDigitiserStarHub = create_spectrum_star_hub_for_testing()

        self._expected_num_channels_each_card = NUM_CHANNELS_PER_DIGITISER_MODULE * NUM_MODULES_PER_DIGITISER
        self._expected_total_num_channels = self._expected_num_channels_each_card * NUM_CARDS_IN_STAR_HUB

        self._all_spectrum_channel_identifiers = [c.value for c in SpectrumAnalogChannelName]
        self._all_spectrum_channel_identifiers.sort()  # Enums are unordered to ensure channels are in ascending order

    def tearDown(self) -> None:
        self._device.disconnect()

    def test_configure_acquisition(self) -> None:
        channels_to_enable = [0, 8]
        acquisition_settings = AcquisitionSettings(
            acquisition_mode=AcquisitionMode.SPC_REC_STD_SINGLE,
            sample_rate_in_hz=int(4e6),
            acquisition_length_in_samples=400,
            pre_trigger_length_in_samples=0,
            timeout_in_ms=1000,
            enabled_channels=channels_to_enable,  # enable only second channel
            vertical_ranges_in_mv=[1000, 2000],
            vertical_offsets_in_percent=[10, 20],
            input_impedances=[InputImpedance.FIFTY_OHM, InputImpedance.ONE_MEGA_OHM],
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
            self._device.analog_channels[channels_to_enable[0]].vertical_range_in_mv,
        )
        self.assertEqual(
            acquisition_settings.vertical_offsets_in_percent[0],
            self._device.analog_channels[channels_to_enable[0]].vertical_offset_in_percent,
        )
        self.assertEqual(
            acquisition_settings.input_impedances[0],
            self._device.analog_channels[channels_to_enable[0]].input_impedance,
        )
        self.assertEqual(
            acquisition_settings.vertical_ranges_in_mv[1],
            self._device.analog_channels[channels_to_enable[1]].vertical_range_in_mv,
        )
        self.assertEqual(
            acquisition_settings.vertical_offsets_in_percent[1],
            self._device.analog_channels[channels_to_enable[1]].vertical_offset_in_percent,
        )
        self.assertEqual(
            acquisition_settings.input_impedances[1],
            self._device.analog_channels[channels_to_enable[1]].input_impedance,
        )

    def test_count_channels(self) -> None:
        channels = self._device.analog_channels
        self.assertEqual(len(channels), self._expected_total_num_channels)

    def test_enable_one_channel(self) -> None:
        with self.assertRaises(SpectrumInvalidNumberOfEnabledChannels):
            self._device.set_enabled_analog_channels([0])

    def test_enable_two_channels(self) -> None:

        self._device.set_enabled_analog_channels([0, self._expected_num_channels_each_card])
        card_one_expected_command = self._all_spectrum_channel_identifiers[0]
        card_two_expected_command = self._all_spectrum_channel_identifiers[0]
        self.assertEqual(
            card_one_expected_command, self._device._child_cards[0].read_spectrum_device_register(SPC_CHENABLE)
        )
        self.assertEqual(
            card_two_expected_command, self._device._child_cards[0].read_spectrum_device_register(SPC_CHENABLE)
        )

    def test_get_channels(self) -> None:
        channels = self._device.analog_channels

        expected_channels = []
        for n in range(NUM_CARDS_IN_STAR_HUB):
            expected_channels += [
                SpectrumDigitiserAnalogChannel(channel_number=i, parent_device=self._device._child_cards[n])
                for i in range(self._expected_num_channels_each_card)
            ]
        expected_channels_tuple = tuple(expected_channels)
        self.assertEqual(expected_channels_tuple, channels)

    def test_transfer_buffer(self) -> None:

        buffer = [
            create_samples_acquisition_transfer_buffer(
                size_in_samples=ACQUISITION_LENGTH, bytes_per_sample=self._device.bytes_per_sample
            )
            for _ in range(NUM_CARDS_IN_STAR_HUB)
        ]
        self._device.define_transfer_buffer(buffer)
        self.assertTrue((array(self._device.transfer_buffers) == buffer).all())

    def test_features(self) -> None:
        try:
            feature_list = self._device.feature_list
        except Exception as e:
            self.assertTrue(False, f"raised an exception {e}")
            feature_list = []
        self.assertEqual(len(feature_list), NUM_CARDS_IN_STAR_HUB)
