from copy import deepcopy
from functools import reduce
from operator import or_
from typing import List, Optional, Sequence, Tuple

from numpy import arange
from numpy.core.records import ndarray

from pyspecde.hardware_model.spectrum_device import (
    SpectrumDevice,
)
from pyspecde.hardware_model.spectrum_card import SpectrumCard, spectrum_card_factory
from pyspecde.exceptions import SpectrumSettingsMismatchError
from pyspecde.hardware_model.spectrum_interface import (
    SpectrumChannelInterface,
    SpectrumIntLengths,
)
from pyspecde.spectrum_api_wrapper import (
    DEVICE_HANDLE_TYPE,
    AcquisitionMode,
    ClockMode,
    spectrum_handle_factory,
    destroy_handle,
)
from pyspecde.spectrum_api_wrapper.status import STAR_HUB_STATUS_TYPE
from pyspecde.spectrum_api_wrapper.io_lines import AvailableIOModes
from pyspecde.spectrum_api_wrapper.triggering import TriggerSource, ExternalTriggerMode
from pyspecde.spectrum_api_wrapper.card_features import CardFeature, AdvancedCardFeature
from pyspecde.spectrum_api_wrapper.transfer_buffer import TransferBuffer
from pyspecde.spectrum_api_wrapper.spectrum_gmbh.regs import SPC_SYNC_ENABLEMASK, SPC_PCIFEATURES


class SpectrumStarHub(SpectrumDevice):
    """Composite of SpectrumDevices"""

    def __init__(
        self,
        hub_handle: DEVICE_HANDLE_TYPE,
        child_cards: Sequence[SpectrumCard],
        master_card_index: int,
    ):
        self._connected = True
        self._child_cards = child_cards
        self._master_card = child_cards[master_card_index]
        self._triggering_card = child_cards[master_card_index]
        child_card_logical_indices = (2 ** n for n in range(len(self._child_cards)))
        self._hub_handle = hub_handle
        all_cards_binary_mask = reduce(or_, child_card_logical_indices)
        self.set_spectrum_api_param(SPC_SYNC_ENABLEMASK, all_cards_binary_mask)

    def disconnect(self) -> None:
        if self._connected:
            destroy_handle(self._hub_handle)
        for card in self._child_cards:
            card.disconnect()
        self._connected = False

    @property
    def status(self) -> STAR_HUB_STATUS_TYPE:
        return STAR_HUB_STATUS_TYPE([card.status for card in self._child_cards])

    def start_transfer(self) -> None:
        for card in self._child_cards:
            card.start_transfer()

    def stop_transfer(self) -> None:
        for card in self._child_cards:
            card.stop_transfer()

    def wait_for_transfer_to_complete(self) -> None:
        for card in self._child_cards:
            card.wait_for_transfer_to_complete()

    @property
    def handle(self) -> DEVICE_HANDLE_TYPE:
        return self._hub_handle

    @property
    def connected(self) -> bool:
        return self._connected

    def set_triggering_card(self, card_index: int) -> None:
        self._triggering_card = self._child_cards[card_index]

    @property
    def clock_mode(self) -> ClockMode:
        return self._master_card.clock_mode

    def set_clock_mode(self, mode: ClockMode) -> None:
        self._master_card.set_clock_mode(mode)

    @property
    def sample_rate_hz(self) -> int:
        return self._master_card.sample_rate_hz

    def set_sample_rate_hz(self, rate: int) -> None:
        for card in self._child_cards:
            card.set_sample_rate_hz(rate)

    @property
    def trigger_sources(self) -> List[TriggerSource]:
        return self._triggering_card.trigger_sources

    def set_trigger_sources(self, sources: List[TriggerSource]) -> None:
        self._triggering_card.set_trigger_sources(sources)
        for card in self._child_cards:
            if card is not self._triggering_card:
                card.set_trigger_sources([TriggerSource.SPC_TM_NONE])

    @property
    def external_trigger_mode(self) -> ExternalTriggerMode:
        return self._triggering_card.external_trigger_mode

    def set_external_trigger_mode(self, mode: ExternalTriggerMode) -> None:
        self._triggering_card.set_external_trigger_mode(mode)

    @property
    def external_trigger_level_mv(self) -> int:
        return self._triggering_card.external_trigger_level_mv

    def set_external_trigger_level_mv(self, level: int) -> None:
        self._triggering_card.set_external_trigger_level_mv(level)

    def apply_channel_enabling(self) -> None:
        for d in self._child_cards:
            d.apply_channel_enabling()

    @property
    def enabled_channels(self) -> List[int]:
        enabled_channels = []
        n_channels_in_previous_card = 0
        for card in self._child_cards:
            enabled_channels += [channel_num + n_channels_in_previous_card for channel_num in card.enabled_channels]
            n_channels_in_previous_card = len(card.channels)
        return enabled_channels

    def set_enabled_channels(self, channels_nums: List[int]) -> None:

        channels_to_enable_all_cards = channels_nums

        for child_card in self._child_cards:
            n_channels_in_card = len(child_card.channels)
            channels_to_enable_this_card = list(set(arange(n_channels_in_card)) & set(channels_to_enable_all_cards))
            num_channels_to_enable_this_card = len(channels_to_enable_this_card)
            child_card.set_enabled_channels(channels_to_enable_this_card)
            channels_to_enable_all_cards = [
                num - n_channels_in_card for num in channels_nums[num_channels_to_enable_this_card:]
            ]

    @property
    def transfer_buffers(self) -> List[TransferBuffer]:
        return [card.transfer_buffers[0] for card in self._child_cards]

    def define_transfer_buffer(self, buffer: Optional[TransferBuffer] = None) -> None:
        if buffer:
            buffers = [deepcopy(buffer) for _ in range(len(self._child_cards))]
            for card, buffer in zip(self._child_cards, buffers):
                card.define_transfer_buffer(buffer)
        else:
            for card in self._child_cards:
                card.define_transfer_buffer()

    def wait_for_acquisition_to_complete(self) -> None:
        for card in self._child_cards:
            card.wait_for_acquisition_to_complete()

    def get_waveforms(self) -> List[ndarray]:
        waveforms = []
        for card in self._child_cards:
            waveforms += card.get_waveforms()
        return waveforms

    @property
    def channels(self) -> List[SpectrumChannelInterface]:
        channels = []
        for device in self._child_cards:
            channels += device.channels
        return channels

    @property
    def acquisition_length_samples(self) -> int:
        lengths = []
        for d in self._child_cards:
            lengths.append(d.acquisition_length_samples)
        return check_settings_constant_across_devices(lengths, __name__)

    def set_acquisition_length_samples(self, length_in_samples: int) -> None:
        for d in self._child_cards:
            d.set_acquisition_length_samples(length_in_samples)

    @property
    def post_trigger_length_samples(self) -> int:
        lengths = []
        for d in self._child_cards:
            lengths.append(d.post_trigger_length_samples)
        return check_settings_constant_across_devices(lengths, __name__)

    def set_post_trigger_length_samples(self, length_in_samples: int) -> None:
        for d in self._child_cards:
            d.set_post_trigger_length_samples(length_in_samples)

    @property
    def acquisition_mode(self) -> AcquisitionMode:
        modes = []
        for d in self._child_cards:
            modes.append(d.acquisition_mode)
        return AcquisitionMode(check_settings_constant_across_devices([m.value for m in modes], __name__))

    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        for d in self._child_cards:
            d.set_acquisition_mode(mode)

    @property
    def timeout_ms(self) -> int:
        timeouts = []
        for d in self._child_cards:
            timeouts.append(d.timeout_ms)
        return check_settings_constant_across_devices(timeouts, __name__)

    @property
    def feature_list(self) -> Tuple[List[CardFeature], List[AdvancedCardFeature]]:
        feature_list_codes = []
        for card in self._child_cards:
            feature_list_codes.append(card.get_spectrum_api_param(SPC_PCIFEATURES))
        check_settings_constant_across_devices(feature_list_codes, __name__)
        return self._child_cards[0].feature_list

    @property
    def available_io_modes(self) -> AvailableIOModes:
        return self._master_card.available_io_modes

    def set_timeout_ms(self, timeout_ms: int) -> None:
        for d in self._child_cards:
            d.set_timeout_ms(timeout_ms)

    def get_spectrum_api_param_all_cards(
        self,
        spectrum_command: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> List[int]:
        param_values_each_device = []
        for card in self._child_cards:
            param_values_each_device.append(card.get_spectrum_api_param(spectrum_command, length))
        return param_values_each_device


def spectrum_star_hub_factory(ip_address: str, num_cards: int, master_card_index: int) -> SpectrumStarHub:
    card_visa_strings = [create_visa_string_from_ip(ip_address, card_num) for card_num in range(num_cards)]
    cards = [spectrum_card_factory(visa_string) for visa_string in card_visa_strings]
    hub_handle = spectrum_handle_factory("sync0")
    return SpectrumStarHub(hub_handle, cards, master_card_index)


def are_all_values_equal(values: List[int]) -> bool:
    return len(set(values)) == 1


def check_settings_constant_across_devices(values: List[int], setting_name: str) -> int:
    if are_all_values_equal(values):
        return values[0]
    else:
        raise SpectrumSettingsMismatchError(f"Devices have different {setting_name} settings")


def create_visa_string_from_ip(ip_address: str, instrument_number: int) -> str:
    return f"TCPIP[0]::{ip_address}::inst{instrument_number}::INSTR"
