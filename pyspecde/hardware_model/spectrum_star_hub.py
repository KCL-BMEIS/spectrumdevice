from copy import deepcopy
from functools import reduce
from operator import or_
from typing import List, Sequence

from pyspecde.hardware_model.spectrum_device import (
    SpectrumDevice,
)
from pyspecde.hardware_model.spectrum_card import SpectrumCard, spectrum_card_factory
from pyspecde.spectrum_exceptions import SpectrumSettingsMismatchError
from pyspecde.hardware_model.spectrum_interface import (
    SpectrumChannelInterface,
    SpectrumIntLengths,
)
from pyspecde.sdk_translation_layer import (
    DEVICE_HANDLE_TYPE,
    TransferBuffer,
    AcquisitionMode,
    TriggerSource,
    ExternalTriggerMode,
    ClockMode,
    spectrum_handle_factory,
    destroy_handle,
)
from third_party.specde.py_header.regs import SPC_SYNC_ENABLEMASK


class SpectrumStarHub(SpectrumDevice):
    def __init__(
        self,
        hub_handle: DEVICE_HANDLE_TYPE,
        child_cards: Sequence[SpectrumCard],
        master_card_index: int,
    ):
        self._child_cards = child_cards
        self._master_card = child_cards[master_card_index]
        self._triggering_card = child_cards[master_card_index]
        child_card_logical_indices = (2 ** n for n in range(len(self._child_cards)))
        self._hub_handle = hub_handle
        all_cards_binary_mask = reduce(or_, child_card_logical_indices)
        self.set_spectrum_api_param(SPC_SYNC_ENABLEMASK, all_cards_binary_mask)
        self._transfer_buffers: List[TransferBuffer] = []

    def disconnect(self) -> None:
        destroy_handle(self._hub_handle)
        for card in self._child_cards:
            card.disconnect()

    def start_dma(self) -> None:
        for card in self._child_cards:
            card.start_dma()

    def stop_dma(self) -> None:
        for card in self._child_cards:
            card.stop_dma()

    @property
    def handle(self) -> DEVICE_HANDLE_TYPE:
        return self._hub_handle

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
    def transfer_buffer(self) -> TransferBuffer:
        raise NotImplementedError(
            "StarHubs create one transfer buffer per device. Access them using the " ".transfer_buffers property."
        )

    @property
    def transfer_buffers(self) -> List[TransferBuffer]:
        return self._transfer_buffers

    def set_transfer_buffer(self, buffer: TransferBuffer) -> None:
        self._transfer_buffers = [deepcopy(buffer) for _ in range(len(self._child_cards))]
        for card, buffer in zip(self._child_cards, self._transfer_buffers):
            card.set_transfer_buffer(buffer)

    @property
    def channels(self) -> List[SpectrumChannelInterface]:
        channels = []
        for device in self._child_cards:
            channels += device.channels
        return channels

    @property
    def acquisition_length_bytes(self) -> int:
        lengths = []
        for d in self._child_cards:
            lengths.append(d.acquisition_length_bytes)
        return check_settings_constant_across_devices(lengths, __name__)

    def set_acquisition_length_bytes(self, length_in_bytes: int) -> None:
        for d in self._child_cards:
            d.set_acquisition_length_bytes(length_in_bytes)

    @property
    def post_trigger_length_bytes(self) -> int:
        lengths = []
        for d in self._child_cards:
            lengths.append(d.post_trigger_length_bytes)
        return check_settings_constant_across_devices(lengths, __name__)

    def set_post_trigger_length_bytes(self, length_in_bytes: int) -> None:
        for d in self._child_cards:
            d.set_post_trigger_length_bytes(length_in_bytes)

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


def spectrum_star_hub_factory(ip_address: str, num_cards: int) -> SpectrumStarHub:
    card_visa_strings = [create_visa_string_from_ip(ip_address, card_num) for card_num in range(num_cards)]
    cards = [spectrum_card_factory(visa_string) for visa_string in card_visa_strings]
    hub_handle = spectrum_handle_factory("sync0")
    return SpectrumStarHub(hub_handle, cards, 0)


def are_all_values_equal(values: List[int]) -> bool:
    return len(set(values)) == 1


def check_settings_constant_across_devices(values: List[int], setting_name: str) -> int:
    if are_all_values_equal(values):
        return values[0]
    else:
        raise SpectrumSettingsMismatchError(f"Devices have different {setting_name} settings")


def create_visa_string_from_ip(ip_address: str, instrument_number: int) -> str:
    return f"TCPIP::{ip_address}::inst{instrument_number}::INSTR"
