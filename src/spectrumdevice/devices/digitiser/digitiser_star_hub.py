"""Provides a concrete class for controlling Spectrum digitiser StarHubs."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.
import datetime
from threading import Thread
from typing import Dict, List, Optional, Sequence

from numpy import float_
from numpy.typing import NDArray

from spectrumdevice.devices.abstract_device import (
    AbstractSpectrumStarHub,
)
from spectrumdevice.devices.abstract_device.abstract_spectrum_hub import check_settings_constant_across_devices
from spectrumdevice.devices.digitiser.digitiser_card import SpectrumDigitiserCard
from spectrumdevice.devices.digitiser.abstract_spectrum_digitiser import AbstractSpectrumDigitiser
from spectrumdevice.settings import ModelNumber, TransferBuffer
from spectrumdevice.settings.card_dependent_properties import CardType
from spectrumdevice.settings.device_modes import AcquisitionMode


class SpectrumDigitiserStarHub(AbstractSpectrumStarHub[SpectrumDigitiserCard], AbstractSpectrumDigitiser):
    """Composite class of `SpectrumDigitiserCard` for controlling a StarHub digitiser device, for example the Spectrum
    NetBox. StarHub digitiser devices are composites of more than one Spectrum digitiser card. Acquisition from the
    child cards of a StarHub is synchronised, aggregating the channels of all child cards. This class enables the
    control of a StarHub device as if it were a single Spectrum card."""

    def __init__(self, device_number: int, child_cards: tuple[SpectrumDigitiserCard, ...], master_card_index: int):
        """
        Args:
            device_number (int): The index of the StarHub to connect to. If only one StarHub is present, set to 0.
            child_cards (Sequence[`SpectrumDigitiserCard`]): A list of `SpectrumCard` objects defining the child cards
                located within the StarHub, correctly constructed with their IP addresses and/or device numbers.
            master_card_index (int): The position within child_cards where the master card (the card which controls the
                clock) is located.
        """
        super().__init__(device_number=device_number, child_cards=child_cards, master_card_index=master_card_index)
        self._acquisition_mode = self.acquisition_mode

    def define_transfer_buffer(self, buffer: Optional[Sequence[TransferBuffer]] = None) -> None:
        """Create or provide `CardToPCDataTransferBuffer` objects for receiving acquired samples from the child cards.
        If no buffers are provided, they will be created with the correct size and a board_memory_offset_bytes of 0. See
        `SpectrumDigitiserCard.define_transfer_buffer()` for more information

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
        """Wait for each card to finish its acquisition. See `SpectrumDigitiserCard.wait_for_acquisition_to_complete()`
        for more information."""
        for card in self._child_cards:
            card.wait_for_acquisition_to_complete()

    def get_waveforms(self) -> List[List[NDArray[float_]]]:
        """Get a list of the most recently transferred waveforms.

        This method gets the waveforms from each child card and joins them into a new list, ordered by channel number.
        See `SpectrumDigitiserCard.get_waveforms()` for more information.

        Args:
            num_acquisitions (int): For FIFO mode:  the number of acquisitions (i.e. trigger events) to wait for and
            copy. Acquiring in batches (num_acquisitions > 1) can improve performance.

        Returns:
            waveforms (List[List[NDArray[float_]]]): A list lists of 1D numpy arrays, one inner list per acquisition,
              and one array per enabled channel, in channel order.
        """
        card_ids_and_waveform_sets: Dict[str, list[list[NDArray[float_]]]] = {}

        def _get_waveforms(digitiser_card: SpectrumDigitiserCard) -> None:
            this_cards_waveforms = digitiser_card.get_waveforms()
            card_ids_and_waveform_sets[str(digitiser_card)] = this_cards_waveforms

        threads = [Thread(target=_get_waveforms, args=(card,)) for card in self._child_cards]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        waveform_sets_all_cards_ordered = []
        for n in range(self.batch_size):
            waveforms_in_this_batch = []
            for card in self._child_cards:
                waveforms_in_this_batch += card_ids_and_waveform_sets[str(card)][n]
            waveform_sets_all_cards_ordered.append(waveforms_in_this_batch)

        return waveform_sets_all_cards_ordered

    def get_timestamp(self) -> Optional[datetime.datetime]:
        """Get timestamp for the last acquisition"""
        return self._triggering_card.get_timestamp()

    def enable_timestamping(self) -> None:
        self._triggering_card.enable_timestamping()

    @property
    def acquisition_length_in_samples(self) -> int:
        """The currently set recording length, which should be the same for all child cards. If different recording
        lengths are set, an exception is raised. See `SpectrumDigitiserCard.acquisition_length_in_samples` for more
        information.

        Returns:
            length_in_samples: The currently set acquisition length in samples."""
        lengths = []
        for d in self._child_cards:
            lengths.append(d.acquisition_length_in_samples)
        return check_settings_constant_across_devices(lengths, __name__)

    def set_acquisition_length_in_samples(self, length_in_samples: int) -> None:
        """Set a new recording length for all child cards. See `SpectrumDigitiserCard.set_acquisition_length_in_samples()`
        for more information.

        Args:
            length_in_samples (int): The desired acquisition length in samples."""
        for d in self._child_cards:
            d.set_acquisition_length_in_samples(length_in_samples)

    @property
    def post_trigger_length_in_samples(self) -> int:
        """The number of samples recorded after a trigger is received. This should be consistent across all child
        cards. If different values are found across the child cards, an exception is raised. See
        `SpectrumDigitiserCard.post_trigger_length_in_samples` for more information.

        Returns:
            length_in_samples (int): The current post trigger length in samples.
        """
        lengths = []
        for d in self._child_cards:
            lengths.append(d.post_trigger_length_in_samples)
        return check_settings_constant_across_devices(lengths, __name__)

    def set_post_trigger_length_in_samples(self, length_in_samples: int) -> None:
        """Set a new post trigger length for all child cards. See `SpectrumDigitiserCard.set_post_trigger_length_in_samples()`
        for more information.

        Args:
            length_in_samples (int): The desired post trigger length in samples.
        """
        for d in self._child_cards:
            d.set_post_trigger_length_in_samples(length_in_samples)

    @property
    def acquisition_mode(self) -> AcquisitionMode:
        """The acquisition mode, which should be the same for all child cards. If it's not, an exception is raised.
        See `SpectrumDigitiserCard.acquisition_mode` for more information.

        Returns:
            mode (`AcquisitionMode`): The currently enabled acquisition mode.
        """
        modes = []
        for d in self._child_cards:
            modes.append(d.acquisition_mode)
        return AcquisitionMode(check_settings_constant_across_devices([m.value for m in modes], __name__))

    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        """Change the acquisition mode for all child cards. See `SpectrumDigitiserCard.set_acquisition_mode()` for more
        information.

        Args:
            mode (`AcquisitionMode`): The desired acquisition mode."""
        for d in self._child_cards:
            d.set_acquisition_mode(mode)

    @property
    def batch_size(self) -> int:
        batch_sizes = []
        for d in self._child_cards:
            batch_sizes.append(d.batch_size)
        return check_settings_constant_across_devices(batch_sizes, __name__)

    def set_batch_size(self, batch_size: int) -> None:
        for d in self._child_cards:
            d.set_batch_size(batch_size)

    def force_trigger_event(self) -> None:
        for d in self._child_cards:
            d.force_trigger_event()

    @property
    def type(self) -> CardType:
        return self._child_cards[0].type

    @property
    def model_number(self) -> ModelNumber:
        return self._child_cards[0].model_number
