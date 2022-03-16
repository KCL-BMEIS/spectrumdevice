"""Provides a concrete class for controlling Spectrum digitiser StarHubs."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.
import datetime
from functools import reduce
from operator import or_
from typing import List, Optional, Sequence, Tuple

from numpy import arange, float_
from numpy.typing import NDArray

from spectrumdevice.devices.spectrum_channel import SpectrumChannel
from spectrumdevice.devices.spectrum_device import SpectrumDevice
from spectrumdevice.devices.spectrum_card import SpectrumCard
from spectrumdevice.exceptions import SpectrumSettingsMismatchError
from spectrumdevice.settings.device_modes import AcquisitionMode, ClockMode
from spectrumdevice.spectrum_wrapper import destroy_handle
from spectrumdevice.settings.status import STAR_HUB_STATUS_TYPE
from spectrumdevice.settings.io_lines import AvailableIOModes
from spectrumdevice.settings.triggering import TriggerSource, ExternalTriggerMode
from spectrumdevice.settings.card_features import CardFeature, AdvancedCardFeature
from spectrumdevice.settings.transfer_buffer import TransferBuffer, CardToPCDataTransferBuffer
from spectrum_gmbh.regs import SPC_SYNC_ENABLEMASK


class SpectrumStarHub(SpectrumDevice):
    """Composite class of `SpectrumCards` for controlling a StarHub device, for example the Spectrum NetBox. StarHub
    devices are composites of more than one Spectrum card. Acquisition from the child cards of a StarHub is
    synchronised, aggregating the channels of all child cards. This class enables the control of a StarHub device as if
    it were a single Spectrum card."""

    def __init__(
        self,
        device_number: int,
        child_cards: Sequence[SpectrumCard],
        master_card_index: int,
    ):
        """
        Args:
            device_number (int): The index of the StarHub to connect to. If only one StarHub is present, set to 0.
            child_cards (Sequence[`SpectrumCard`]): A list of `SpectrumCard` objects defining the child cards located
                within the StarHub, including their IP addresses and/or device numbers.
            master_card_index (int): The position within child_cards where the master card (the card which controls the
                clock) is located.
        """
        self._child_cards = child_cards
        self._master_card = child_cards[master_card_index]
        self._triggering_card = child_cards[master_card_index]
        child_card_logical_indices = (2**n for n in range(len(self._child_cards)))
        self._visa_string = f"sync{device_number}"
        self._connect(self._visa_string)
        all_cards_binary_mask = reduce(or_, child_card_logical_indices)
        self.write_to_spectrum_device_register(SPC_SYNC_ENABLEMASK, all_cards_binary_mask)
        self._acquisition_mode = self.acquisition_mode

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
    def status(self) -> STAR_HUB_STATUS_TYPE:
        """The statuses of each child card, in a list. See `SpectrumCard.status` for more information.
        Returns:
            statuses (List[List[`CardStatus`]]): A list of lists of `CardStatus`.
        """
        return STAR_HUB_STATUS_TYPE([card.status for card in self._child_cards])

    def start_transfer(self) -> None:
        """Start the transfer of samples from the on-device buffer of each child card to its `TransferBuffer`. See
        `SpectrumCard.start_transfer()` for more information."""
        for card in self._child_cards:
            card.start_transfer()

    def stop_transfer(self) -> None:
        """Stop the transfer of samples from each card to its `TransferBuffer`. See `SpectrumCard.stop_transfer()` for
        more information."""
        for card in self._child_cards:
            card.stop_transfer()

    def wait_for_transfer_to_complete(self) -> None:
        """Wait for all cards to stop transferring samples to their `TransferBuffers`. See
        `SpectrumCard.wait_for_transfer_to_complete()` for more information."""
        for card in self._child_cards:
            card.wait_for_transfer_to_complete()

    @property
    def connected(self) -> bool:
        """True if a StarHub is connected, False if not."""
        return self._connected

    def set_triggering_card(self, card_index: int) -> None:
        """Change the index of the child_card responsible for receiving a trigger. During construction, this is set
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
        `SpectrumCard.trigger_sources()` for more information.

        Returns:
            sources (List[`TriggerSource`]): A list of the currently enabled trigger sources."""
        return self._triggering_card.trigger_sources

    def set_trigger_sources(self, sources: List[TriggerSource]) -> None:
        """Change the trigger sources configured on the triggering card, which by default is the master card. See
        `SpectrumCard.trigger_sources()` for more information.

        Args:
            sources (List[`TriggerSource`]): The trigger sources to enable, in a list."""
        self._triggering_card.set_trigger_sources(sources)
        for card in self._child_cards:
            if card is not self._triggering_card:
                card.set_trigger_sources([TriggerSource.SPC_TMASK_NONE])

    @property
    def external_trigger_mode(self) -> ExternalTriggerMode:
        """The trigger mode configured on the triggering card, which by default is the master card. See
        `SpectrumCard.external_trigger_mode()` for more information.

        Returns:
            mode (`ExternalTriggerMode`): The currently set external trigger mode.
        """
        return self._triggering_card.external_trigger_mode

    def set_external_trigger_mode(self, mode: ExternalTriggerMode) -> None:
        """Change the trigger mode configured on the triggering card, which by default is the master card. See
        `SpectrumCard.set_external_trigger_mode()` for more information.

        Args:
            mode (`ExternalTriggerMode`): The desired external trigger mode."""
        self._triggering_card.set_external_trigger_mode(mode)

    @property
    def external_trigger_level_in_mv(self) -> int:
        """The external trigger level configured on the triggering card, which by default is the master card. See
        `SpectrumCard.external_trigger_level_mv()` for more information.

        Returns:
            level (int): The external trigger level in mV.
        """
        return self._triggering_card.external_trigger_level_in_mv

    def set_external_trigger_level_in_mv(self, level: int) -> None:
        """Change the external trigger level configured on the triggering card, which by default is the master card.
        See `SpectrumCard.set_external_trigger_level_mv()` for more information.

        Args:
            level (int): The desired external trigger level in mV.
        """
        self._triggering_card.set_external_trigger_level_in_mv(level)

    @property
    def external_trigger_pulse_width_in_samples(self) -> int:
        """The trigger pulse width (samples) configured on the triggering card, which by default is the master card.
        See `SpectrumCard.external_trigger_pulse_width_in_samples()` for more information.

        Returns:
            width (int): The current trigger pulse width in samples.
        """
        return self._triggering_card.external_trigger_pulse_width_in_samples

    def set_external_trigger_pulse_width_in_samples(self, width: int) -> None:
        """Change the trigger pulse width (samples) configured on the triggering card, which by default is the master
        card. See `SpectrumCard.set_external_trigger_pulse_width_in_samples()` for more information.

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
        """The `TransferBuffer`s of all of the child cards of the hub. See `SpectrumCard.transfer_buffers` for more
        information.

        Returns:
            buffers (List[`TransferBuffer`]): A list of the transfer buffers for each child card."""
        return [card.transfer_buffers[0] for card in self._child_cards]

    def define_transfer_buffer(self, buffer: Optional[List[CardToPCDataTransferBuffer]] = None) -> None:
        """Create or provide `CardToPCDataTransferBuffer` objects for receiving acquired samples from the child cards. If
        no buffers are provided, they will be created with the correct size and a board_memory_offset_bytes of 0. See
        `SpectrumCard.define_transfer_buffer()` for more information

        Args:
            buffer (Optional[`CardToPCDataTransferBuffer`]): A list containing pre-constructed
            `CardToPCDataTransferBuffer` objects, one for each child card. The size of the buffers should be chosen
            according to the current number of active channels in each card and the acquisition length.
        """
        if buffer:
            for card, buff in zip(self._child_cards, buffer):
                card.define_transfer_buffer([buff])
        else:
            for card in self._child_cards:
                card.define_transfer_buffer()

    def wait_for_acquisition_to_complete(self) -> None:
        """Wait for each card to finish its acquisition. See `SpectrumCard.wait_for_acquisition_to_complete()` for more
        information."""
        for card in self._child_cards:
            card.wait_for_acquisition_to_complete()

    def get_waveforms(self) -> List[NDArray[float_]]:
        """Get a list of of the most recently transferred waveforms.

        This method gets the waveforms from each child card and joins them into a new list, ordered by channel number.
        See `SpectrumCard.get_waveforms()` for more information.

        Returns:
            waveforms (List[NDArray[float_]]): A list of 1D numpy arrays, one per enabled channel, in channel order.
        """
        waveforms_all_cards = []
        for card in self._child_cards:
            waveforms_all_cards += card.get_waveforms()

        return waveforms_all_cards

    def get_timestamp(self) -> Optional[datetime.datetime]:
        """Get timestamp for the last acquisition"""
        return self._triggering_card.get_timestamp()

    def enable_timestamping(self) -> None:
        self._triggering_card.enable_timestamping()

    @property
    def channels(self) -> Sequence[SpectrumChannel]:
        """A tuple containing of all the channels of the child cards of the hub. See `SpectrumCard.channels` for more
        information.

        Returns:
            channels (List[`SpectrumChannel`]): A list of `SpectrumChannel` objects.
        """
        channels: List[SpectrumChannel] = []
        for device in self._child_cards:
            channels += device.channels
        return tuple(channels)

    @property
    def acquisition_length_in_samples(self) -> int:
        """The currently set recording length, which should be the same for all child cards. If different recording
        lengths are set, an exception is raised. See `SpectrumCard.acquisition_length_in_samples` for more information.

        Returns:
            length_in_samples: The currently set acquisition length in samples."""
        lengths = []
        for d in self._child_cards:
            lengths.append(d.acquisition_length_in_samples)
        return _check_settings_constant_across_devices(lengths, __name__)

    def set_acquisition_length_in_samples(self, length_in_samples: int) -> None:
        """Set a new recording length for all child cards. See `SpectrumCard.set_acquisition_length_in_samples()` for
        more information.

        Args:
            length_in_samples (int): The desired acquisition length in samples."""
        for d in self._child_cards:
            d.set_acquisition_length_in_samples(length_in_samples)

    @property
    def post_trigger_length_in_samples(self) -> int:
        """The number of samples recorded after a trigger is receive. This should be consistent across all child
        cards. If different values are found across the child cards, an exception is raised. See
        `SpectrumCard.post_trigger_length_in_samples` for more information.

        Returns:
            length_in_samples (int): The current post trigger length in samples.
        """
        lengths = []
        for d in self._child_cards:
            lengths.append(d.post_trigger_length_in_samples)
        return _check_settings_constant_across_devices(lengths, __name__)

    def set_post_trigger_length_in_samples(self, length_in_samples: int) -> None:
        """Set a new post trigger length for all child cards. See `SpectrumCard.set_post_trigger_length_in_samples()`
        for more information.

        Args:
            length_in_samples (int): The desired post trigger length in samples.
        """
        for d in self._child_cards:
            d.set_post_trigger_length_in_samples(length_in_samples)

    @property
    def acquisition_mode(self) -> AcquisitionMode:
        """The acquisition mode, which should be the same for all child cards. If it's not, an exception is raised.
        See `SpectrumCard.acquisition_mode` for more information.

        Returns:
            mode (`AcquisitionMode`): The currently enabled acquisition mode.
        """
        modes = []
        for d in self._child_cards:
            modes.append(d.acquisition_mode)
        return AcquisitionMode(_check_settings_constant_across_devices([m.value for m in modes], __name__))

    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        """Change the acquisition mode for all child cards. See `SpectrumCard.set_acquisition_mode()` for more
        information.

        Args:
            mode (`AcquisitionMode`): The desired acquisition mode."""
        for d in self._child_cards:
            d.set_acquisition_mode(mode)

    @property
    def timeout_in_ms(self) -> int:
        """The time for which the card will wait for a trigger to tbe received after an acquisition has started
        before returning an error. This should be the same for all child cards. If it's not, an exception is raised.

        Returns:
            timeout_ms (int): The currently set acquisition timeout in ms.
        """
        timeouts = []
        for d in self._child_cards:
            timeouts.append(d.timeout_in_ms)
        return _check_settings_constant_across_devices(timeouts, __name__)

    def set_timeout_in_ms(self, timeout_ms: int) -> None:
        """Change the acquisition timeout value for all child cards.

        Args:
            timeout_ms (int): The desired acquisition timeout setting in seconds."""
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


def _check_settings_constant_across_devices(values: List[int], setting_name: str) -> int:
    if _are_all_values_equal(values):
        return values[0]
    else:
        raise SpectrumSettingsMismatchError(f"Devices have different {setting_name} settings")
