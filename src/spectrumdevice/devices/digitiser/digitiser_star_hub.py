"""Provides a concrete class for controlling Spectrum digitiser StarHubs."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.
import datetime
from typing import List, Optional, Sequence, cast

from numpy import float_
from numpy.typing import NDArray

from spectrumdevice.devices.abstract_device.abstract_spectrum_hub import (
    AbstractSpectrumStarHub,
    check_settings_constant_across_devices,
)
from spectrumdevice.devices.digitiser.abstract_spectrum_digitiser import AbstractSpectrumDigitiser
from spectrumdevice.devices.digitiser.digitiser_card import SpectrumDigitiserCard
from spectrumdevice.settings.device_modes import AcquisitionMode
from spectrumdevice.settings.transfer_buffer import CardToPCDataTransferBuffer


class SpectrumDigitiserStarHub(AbstractSpectrumStarHub, AbstractSpectrumDigitiser):
    """Composite class of `SpectrumCards` for controlling a StarHub abstract_device, for example the Spectrum NetBox. StarHub
    devices are composites of more than one Spectrum card. Acquisition from the child cards of a StarHub is
    synchronised, aggregating the channels of all child cards. This class enables the control of a StarHub abstract_device as if
    it were a single Spectrum card."""

    def __init__(
        self,
        device_number: int,
        child_cards: Sequence[SpectrumDigitiserCard],
        master_card_index: int,
    ):
        """
        Args:
            device_number (int): The index of the StarHub to connect to. If only one StarHub is present, set to 0.
            child_cards (Sequence[`SpectrumDigitiserCard`]): A list of `SpectrumCard` objects defining the child cards located
                within the StarHub, including their IP addresses and/or abstract_device numbers.
            master_card_index (int): The position within child_cards where the master card (the card which controls the
                clock) is located.
        """
        AbstractSpectrumStarHub.__init__(self, device_number, child_cards, master_card_index)
        self._acquisition_mode = self.acquisition_mode

    def define_transfer_buffer(self, buffer: Optional[List[CardToPCDataTransferBuffer]] = None) -> None:
        """Create or provide `CardToPCDataTransferBuffer` objects for receiving acquired samples from the child cards. If
        no buffers are provided, they will be created with the correct size and a board_memory_offset_bytes of 0. See
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
        """Wait for each card to finish its acquisition. See `SpectrumDigitiserCard.wait_for_acquisition_to_complete()` for more
        information."""
        for card in self._child_cards:
            cast(SpectrumDigitiserCard, card).wait_for_acquisition_to_complete()

    def get_waveforms(self) -> List[NDArray[float_]]:
        """Get a list of of the most recently transferred waveforms.

        This method gets the waveforms from each child card and joins them into a new list, ordered by channel number.
        See `SpectrumDigitiserCard.get_waveforms()` for more information.

        Returns:
            waveforms (List[NDArray[float_]]): A list of 1D numpy arrays, one per enabled channel, in channel order.
        """
        waveforms_all_cards = []
        for card in self._child_cards:
            waveforms_all_cards += cast(SpectrumDigitiserCard, card).get_waveforms()

        return waveforms_all_cards

    def get_timestamp(self) -> Optional[datetime.datetime]:
        """Get timestamp for the last acquisition"""
        return cast(SpectrumDigitiserCard, self._triggering_card).get_timestamp()

    def enable_timestamping(self) -> None:
        cast(SpectrumDigitiserCard, self._triggering_card).enable_timestamping()

    @property
    def acquisition_length_in_samples(self) -> int:
        """The currently set recording length, which should be the same for all child cards. If different recording
        lengths are set, an exception is raised. See `SpectrumDigitiserCard.acquisition_length_in_samples` for more information.

        Returns:
            length_in_samples: The currently set acquisition length in samples."""
        lengths = []
        for d in self._child_cards:
            lengths.append(cast(SpectrumDigitiserCard, d).acquisition_length_in_samples)
        return check_settings_constant_across_devices(lengths, __name__)

    def set_acquisition_length_in_samples(self, length_in_samples: int) -> None:
        """Set a new recording length for all child cards. See `SpectrumDigitiserCard.set_acquisition_length_in_samples()` for
        more information.

        Args:
            length_in_samples (int): The desired acquisition length in samples."""
        for d in self._child_cards:
            cast(SpectrumDigitiserCard, d).set_acquisition_length_in_samples(length_in_samples)

    @property
    def post_trigger_length_in_samples(self) -> int:
        """The number of samples recorded after a trigger is receive. This should be consistent across all child
        cards. If different values are found across the child cards, an exception is raised. See
        `SpectrumDigitiserCard.post_trigger_length_in_samples` for more information.

        Returns:
            length_in_samples (int): The current post trigger length in samples.
        """
        lengths = []
        for d in self._child_cards:
            lengths.append(cast(SpectrumDigitiserCard, d).post_trigger_length_in_samples)
        return check_settings_constant_across_devices(lengths, __name__)

    def set_post_trigger_length_in_samples(self, length_in_samples: int) -> None:
        """Set a new post trigger length for all child cards. See `SpectrumDigitiserCard.set_post_trigger_length_in_samples()`
        for more information.

        Args:
            length_in_samples (int): The desired post trigger length in samples.
        """
        for d in self._child_cards:
            cast(SpectrumDigitiserCard, d).set_post_trigger_length_in_samples(length_in_samples)

    @property
    def acquisition_mode(self) -> AcquisitionMode:
        """The acquisition mode, which should be the same for all child cards. If it's not, an exception is raised.
        See `SpectrumDigitiserCard.acquisition_mode` for more information.

        Returns:
            mode (`AcquisitionMode`): The currently enabled acquisition mode.
        """
        modes = []
        for d in self._child_cards:
            modes.append(cast(SpectrumDigitiserCard, d).acquisition_mode)
        return AcquisitionMode(check_settings_constant_across_devices([m.value for m in modes], __name__))

    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        """Change the acquisition mode for all child cards. See `SpectrumDigitiserCard.set_acquisition_mode()` for more
        information.

        Args:
            mode (`AcquisitionMode`): The desired acquisition mode."""
        for d in self._child_cards:
            cast(SpectrumDigitiserCard, d).set_acquisition_mode(mode)
