"""Provides a partially implemented abstract superclass for all Spectrum Star Hubs (as opposed to individual
Spectrum cards)."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from abc import ABC
from functools import reduce
from operator import or_
from typing import List, Sequence, Tuple

from numpy import arange

from spectrum_gmbh.regs import SPC_SYNC_ENABLEMASK
from spectrumdevice.devices.abstract_device.abstract_spectrum_device import AbstractSpectrumDevice
from spectrumdevice.devices.abstract_device.device_interface import SpectrumChannelInterface, SpectrumDeviceInterface
from spectrumdevice.exceptions import SpectrumSettingsMismatchError
from spectrumdevice.settings import (
    AdvancedCardFeature,
    AvailableIOModes,
    CardFeature,
    ClockMode,
    ExternalTriggerMode,
    DEVICE_STATUS_TYPE,
    TransferBuffer,
    TriggerSource,
)
from spectrumdevice.spectrum_wrapper import destroy_handle


class AbstractSpectrumStarHub(AbstractSpectrumDevice, ABC):
    """Composite abstract class of `AbstractSpectrumCard` implementing methods common to all StarHubs. StarHubs are
    composites of more than one Spectrum card. Acquisition and generation from the child cards of a StarHub
    is synchronised, aggregating the channels of all child cards."""

    def __init__(
        self,
        device_number: int,
        child_cards: Sequence[SpectrumDeviceInterface],
        master_card_index: int,
    ):
        """
        Args:
            device_number (int): The index of the StarHub to connect to. If only one StarHub is present, set to 0.
            child_cards (Sequence[`SpectrumDeviceInterface`]): A list of objects representing the child cards located
                within the StarHub, correctly constructed with their IP addresses and/or device numbers.
            master_card_index (int): The position within child_cards where the master card (the card which controls the
                clock) is located.
        """
        self._child_cards: Sequence[SpectrumDeviceInterface] = child_cards
        self._master_card = child_cards[master_card_index]
        self._triggering_card = child_cards[master_card_index]
        child_card_logical_indices = (2**n for n in range(len(self._child_cards)))
        self._visa_string = f"sync{device_number}"
        self._connect(self._visa_string)
        all_cards_binary_mask = reduce(or_, child_card_logical_indices)
        self.write_to_spectrum_device_register(SPC_SYNC_ENABLEMASK, all_cards_binary_mask)

    def disconnect(self) -> None:
        """Disconnects from each child card and terminates connection to the hub itself."""
        if self._connected:
            destroy_handle(self._handle)
        for card in self._child_cards:
            card.disconnect()
        self._connected = False

    def reconnect(self) -> None:
        """Reconnects to the hub after a `disconnect()`, and reconnects to each child card."""
        self._connect(self._visa_string)
        for card in self._child_cards:
            card.reconnect()

    @property
    def status(self) -> DEVICE_STATUS_TYPE:
        """The statuses of each child card, in a list. See `SpectrumDigitiserCard.status` for more information.
        Returns:
            statuses (List[List[`CardStatus`]]): A list of lists of `CardStatus` (each card has a list of statuses).
        """
        return DEVICE_STATUS_TYPE([card.status[0] for card in self._child_cards])

    def start_transfer(self) -> None:
        """Start the transfer of data between the on-device buffer of each child card and its `TransferBuffer`. See
        `AbstractSpectrumCard.start_transfer()` for more information."""
        for card in self._child_cards:
            card.start_transfer()

    def stop_transfer(self) -> None:
        """Stop the transfer of data between each card and its `TransferBuffer`. See
        `AbstractSpectrumCard.stop_transfer()` for more information."""
        for card in self._child_cards:
            card.stop_transfer()

    def wait_for_transfer_to_complete(self) -> None:
        """Wait for all cards to stop transferring data to/from their `TransferBuffers`. See
        `AbstractSpectrumCard.wait_for_transfer_to_complete()` for more information."""
        for card in self._child_cards:
            card.wait_for_transfer_to_complete()

    @property
    def connected(self) -> bool:
        """True if the StarHub is connected, False if not."""
        return self._connected

    def set_triggering_card(self, card_index: int) -> None:
        """Change the index of the child card responsible for receiving a trigger. During construction, this is set
        equal to the index of the master card but in some situations it may be necessary to change it.

        Args:
            card_index (int): The index of the StarHub's triggering card within the list of child cards provided on
                __init__().
        """
        self._triggering_card = self._child_cards[card_index]

    @property
    def clock_mode(self) -> ClockMode:
        """The clock mode currently configured on the master card.

        Returns:
            mode (`ClockMode`): The currently configured clock mode."""
        return self._master_card.clock_mode

    def set_clock_mode(self, mode: ClockMode) -> None:
        """Change the clock mode configured on the master card.

        Args:
            mode (`ClockMode`): The desired clock mode."""
        self._master_card.set_clock_mode(mode)

    @property
    def sample_rate_in_hz(self) -> int:
        """The sample rate configured on the master card.

        Returns:
            rate (int): The current sample rate of the master card in Hz.
        """
        return self._master_card.sample_rate_in_hz

    def set_sample_rate_in_hz(self, rate: int) -> None:
        """Change the sample rate of the child cards (including the master card).
        Args:
            rate (int): The desired sample rate of the child cards in Hz.
        """
        for card in self._child_cards:
            card.set_sample_rate_in_hz(rate)

    @property
    def trigger_sources(self) -> List[TriggerSource]:
        """The trigger sources configured on the triggering card, which by default is the master card. See
        `AbstractSpectrumCard.trigger_sources()` for more information.

        Returns:
            sources (List[`TriggerSource`]): A list of the currently enabled trigger sources."""
        return self._triggering_card.trigger_sources

    def set_trigger_sources(self, sources: List[TriggerSource]) -> None:
        """Change the trigger sources configured on the triggering card, which by default is the master card. See
        `AbstractSpectrumCard.trigger_sources()` for more information.

        Args:
            sources (List[`TriggerSource`]): The trigger sources to enable, in a list."""
        self._triggering_card.set_trigger_sources(sources)
        for card in self._child_cards:
            if card is not self._triggering_card:
                card.set_trigger_sources([TriggerSource.SPC_TMASK_NONE])

    @property
    def external_trigger_mode(self) -> ExternalTriggerMode:
        """The trigger mode configured on the triggering card, which by default is the master card. See
        `AbstractSpectrumCard.external_trigger_mode()` for more information.

        Returns:
            mode (`ExternalTriggerMode`): The currently set external trigger mode.
        """
        return self._triggering_card.external_trigger_mode

    def set_external_trigger_mode(self, mode: ExternalTriggerMode) -> None:
        """Change the trigger mode configured on the triggering card, which by default is the master card. See
        `AbstractSpectrumCard.set_external_trigger_mode()` for more information.

        Args:
            mode (`ExternalTriggerMode`): The desired external trigger mode."""
        self._triggering_card.set_external_trigger_mode(mode)

    @property
    def external_trigger_level_in_mv(self) -> int:
        """The external trigger level configured on the triggering card, which by default is the master card. See
        `AbstractSpectrumCard.external_trigger_level_mv()` for more information.

        Returns:
            level (int): The external trigger level in mV.
        """
        return self._triggering_card.external_trigger_level_in_mv

    def set_external_trigger_level_in_mv(self, level: int) -> None:
        """Change the external trigger level configured on the triggering card, which by default is the master card.
        See `AbstractSpectrumCard.set_external_trigger_level_mv()` for more information.

        Args:
            level (int): The desired external trigger level in mV.
        """
        self._triggering_card.set_external_trigger_level_in_mv(level)

    @property
    def external_trigger_pulse_width_in_samples(self) -> int:
        """The trigger pulse width (samples) configured on the triggering card, which by default is the master card.
        See `AbstractSpectrumCard.external_trigger_pulse_width_in_samples()` for more information.

        Returns:
            width (int): The current trigger pulse width in samples.
        """
        return self._triggering_card.external_trigger_pulse_width_in_samples

    def set_external_trigger_pulse_width_in_samples(self, width: int) -> None:
        """Change the trigger pulse width (samples) configured on the triggering card, which by default is the master
        card. See `AbstractSpectrumCard.set_external_trigger_pulse_width_in_samples()` for more information.

        Args:
            width (int): The desired trigger pulse width in samples.
        """
        self._triggering_card.set_external_trigger_pulse_width_in_samples(width)

    def apply_channel_enabling(self) -> None:
        """Apply the enabled channels chosen using `set_enable_channels()`. This happens automatically and does not
        usually need to be called."""
        for d in self._child_cards:
            d.apply_channel_enabling()

    @property
    def enabled_channels(self) -> List[int]:
        """The currently enabled channel indices, indexed over the whole hub (from 0 to N-1, where N is the total
        number of channels available to the hub).

        Returns:
            channel_nums (List[int]): The currently enabled channel indices.
        """
        enabled_channels = []
        n_channels_in_previous_card = 0
        for card in self._child_cards:
            enabled_channels += [channel_num + n_channels_in_previous_card for channel_num in card.enabled_channels]
            n_channels_in_previous_card = len(card.channels)
        return enabled_channels

    def set_enabled_channels(self, channels_nums: List[int]) -> None:
        """Change the currently enabled channel indices, indexed over the whole hub (from 0 to N-1, where N is the total
        number of channels available to the hub).

        Returns:
            channel_nums (List[int]): The indices to enable.
        """
        channels_nums.sort()
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
        """The `TransferBuffer`s of all the child cards of the hub. See `AbstractSpectrumCard.transfer_buffers` for more
        information.

        Returns:
            buffers (List[`TransferBuffer`]): A list of the transfer buffers for each child card."""
        return [card.transfer_buffers[0] for card in self._child_cards]

    @property
    def channels(self) -> Sequence[SpectrumChannelInterface]:
        """A tuple containing of all the channels of the child cards of the hub. See `AbstractSpectrumCard.channels` for
        more information.

        Returns:
            channels (Sequence[`SpectrumChannelInterface`]): A tuple of `SpectrumDigitiserChannel` objects.
        """
        channels: List[SpectrumChannelInterface] = []
        for device in self._child_cards:
            channels += device.channels
        return tuple(channels)

    @property
    def timeout_in_ms(self) -> int:
        """The time for which the card will wait for a trigger to be received after a device has started
        before returning an error. This should be the same for all child cards. If it's not, an exception is raised.

        Returns:
            timeout_ms (int): The currently set timeout in ms.
        """
        timeouts = []
        for d in self._child_cards:
            timeouts.append(d.timeout_in_ms)
        return check_settings_constant_across_devices(timeouts, __name__)

    def set_timeout_in_ms(self, timeout_ms: int) -> None:
        """Change the timeout value for all child cards.

        Args:
            timeout_ms (int): The desired timeout setting in seconds."""
        for d in self._child_cards:
            d.set_timeout_in_ms(timeout_ms)

    @property
    def feature_list(self) -> List[Tuple[List[CardFeature], List[AdvancedCardFeature]]]:
        """Get a list of the features of the child cards. See `CardFeature`, `AdvancedCardFeature` and the Spectrum
        documentation for more information.

        Returns:
            features (List[Tuple[List[`CardFeature`], List[`AdvancedCardFeature`]]]): A list of tuples, one per child
                card. Each tuple contains a list of features and a list of advanced features for that card.
        """
        return [card.feature_list[0] for card in self._child_cards]

    @property
    def available_io_modes(self) -> AvailableIOModes:
        """For each multipurpose IO line on the master card, read the available modes. See `IOLineMode` and the Spectrum
        Documentation for all possible available modes and their meanings.

        Returns:
            modes (AvailableIOModes): An `AvailableIOModes` dataclass containing the modes available for each IO line.
        """
        return self._master_card.available_io_modes

    def __str__(self) -> str:
        return f"StarHub {self._visa_string}"


def _are_all_values_equal(values: List[int]) -> bool:
    return len(set(values)) == 1


def check_settings_constant_across_devices(values: List[int], setting_name: str) -> int:
    if _are_all_values_equal(values):
        return values[0]
    else:
        raise SpectrumSettingsMismatchError(f"Devices have different {setting_name} settings")
