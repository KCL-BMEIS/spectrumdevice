"""Provides Mock spectrum device classes for testing software when no drivers or hardware are present."""

# Christian Baker, King's College London
# Copyright (c) 2024 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

import logging
from time import perf_counter, sleep
from typing import Any, List, Optional, Sequence

from spectrumdevice.devices.awg.awg_card import SpectrumAWGCard
from spectrumdevice.devices.digitiser import SpectrumDigitiserCard
from spectrumdevice.devices.digitiser import SpectrumDigitiserStarHub
from spectrumdevice.devices.mocks.mock_abstract_devices import (
    MockAbstractSpectrumDigitiser,
    MockAbstractSpectrumCard,
    MockAbstractSpectrumStarHub,
    MockAbstractSpectrumAWG,
)
from spectrumdevice.devices.mocks.mock_waveform_source import TRANSFER_CHUNK_COUNTER
from spectrumdevice.devices.mocks.timestamps import MockTimestamper
from spectrumdevice.exceptions import (
    SpectrumNoTransferBufferDefined,
    SpectrumSettingsMismatchError,
)
from spectrumdevice.settings import AdvancedCardFeature, CardFeature, ModelNumber, TransferBuffer
from spectrumdevice.settings.card_dependent_properties import CardType
from spectrumdevice.settings.device_modes import AcquisitionMode

logger = logging.getLogger(__name__)
MOCK_TRANSFER_TIMEOUT_IN_S = 10


class MockSpectrumDigitiserCard(MockAbstractSpectrumDigitiser, MockAbstractSpectrumCard, SpectrumDigitiserCard):
    """A mock spectrum card, for testing software written to use the `SpectrumDigitiserCard` class.

    This class overrides methods of `SpectrumDigitiserCard` that communicate with hardware with mocked implementations,
    allowing software to be tested without Spectrum hardware connected or drivers installed, e.g. during CI. It overrides
    methods to use to set up a mock 'on-device buffer' attribute into which a mock waveform source will write
    samples. It also uses a MockTimestamper to generated timestamps for mock waveforms.
    """

    def __init__(
        self,
        device_number: int,
        model: ModelNumber,
        mock_source_frame_rate_hz: float,
        num_modules: int,
        num_channels_per_module: int,
        card_features: Optional[list[CardFeature]] = None,
        advanced_card_features: Optional[list[AdvancedCardFeature]] = None,
    ):
        """
        Args:
            device_number (int): The index of the mock device to create. Used to create a name for the device which is
                used internally.
            model (ModelNumber): The model of card to mock. Affects the allowed acquisition and post-trigger lengths.
            mock_source_frame_rate_hz (float): Rate at which waveforms will be generated by the mock source providing
                data to the mock spectrum card.
            num_modules (int): The number of internal modules to assign the mock card. Default 2. On real hardware, this
                is read from the device so does not need to be set. See the Spectrum documentation to work out how many
                modules your hardware has.
            num_channels_per_module (int): The number of channels per module. Default 4 (so 8 channels in total). On
                real hardware, this is read from the device so does not need to be set.
            card_features (list[CardFeature]): List of available features of the mock device
            advanced_card_features (list[AdvancedCardFeature]): List of available advanced features of the mock device

        """

        super().__init__(
            device_number=device_number,
            model=model,
            mock_source_frame_rate_hz=mock_source_frame_rate_hz,
            num_modules=num_modules,
            num_channels_per_module=num_channels_per_module,
            card_type=CardType.SPCM_TYPE_AI,
            card_features=card_features if card_features is not None else [],
            advanced_card_features=advanced_card_features if advanced_card_features is not None else [],
        )
        self._connect(self._visa_string)
        self._acquisition_mode = self.acquisition_mode
        self._previous_transfer_chunk_count = 0
        self._param_dict[TRANSFER_CHUNK_COUNTER] = 0

    def enable_timestamping(self) -> None:
        self._timestamper: MockTimestamper = MockTimestamper(self, self._handle)

    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        """Mock timestamper needs to be recreated if the acquisition mode is changed."""
        super().set_acquisition_mode(mode)
        self._timestamper = MockTimestamper(self, self._handle)

    def set_sample_rate_in_hz(self, rate: int) -> None:
        """Mock timestamper needs to be recreated if the sample rate is changed."""
        super().set_sample_rate_in_hz(rate)
        self._timestamper = MockTimestamper(self, self._handle)

    def set_acquisition_length_in_samples(self, length_in_samples: int) -> None:
        """Set length of mock recording (per channel). In FIFO mode, this will be quantised to the nearest 8 samples.
        See `SpectrumDigitiserCard` for more information. This method is overridden here only so that the internal
        attributes related to the mock on-device buffer can be set.

        Args:
            length_in_samples (int): Number of samples in each generated mock waveform
        """
        super().set_acquisition_length_in_samples(length_in_samples)

    def set_enabled_analog_channels(self, channels_nums: List[int]) -> None:
        """Set the channels to enable for the mock acquisition. See `SpectrumDigitiserCard` for more information. This
        method is overridden here only so that the internal attributes related to the mock on-device buffer
        can be set.

        Args:
            channels_nums (List[int]): List of mock channel indices to enable, e.g. [0, 1, 2].

        """
        if len(list(filter(lambda x: 0 <= x < len(self.analog_channels), channels_nums))) == len(channels_nums):
            super().set_enabled_analog_channels(channels_nums)
        else:
            raise SpectrumSettingsMismatchError("Not enough channels in mock device configuration.")

    def define_transfer_buffer(self, buffer: Optional[Sequence[TransferBuffer]] = None) -> None:
        """Create or provide a `TransferBuffer` object for receiving acquired samples from the device.

        See SpectrumDigitiserCard.define_transfer_buffer(). This mock implementation is identical apart from that it
        does not write to any hardware device."""
        self._set_or_update_transfer_buffer_attribute(buffer)

    def start_transfer(self) -> None:
        """See `SpectrumDigitiserCard.start_transfer()`."""
        pass

    def stop_transfer(self) -> None:
        """See `SpectrumDigitiserCard.stop_transfer()`."""
        pass

    def wait_for_transfer_chunk_to_complete(self) -> None:
        """See `SpectrumDigitiserCard.wait_for_transfer_chunk_to_complete()`. This mock implementation blocks until a
        new mock transfer has been completed by waiting for a change to TRANSFER_CHUNK_COUNTER."""
        if self._transfer_buffer:
            t0 = perf_counter()
            t_elapsed = 0.0
            while (
                self._previous_transfer_chunk_count == self._param_dict[TRANSFER_CHUNK_COUNTER]
            ) and t_elapsed < MOCK_TRANSFER_TIMEOUT_IN_S:
                sleep(0.1)
                t_elapsed = perf_counter() - t0
            self._previous_transfer_chunk_count = self._param_dict[TRANSFER_CHUNK_COUNTER]
        else:
            raise SpectrumNoTransferBufferDefined("No transfer in progress.")

    def wait_for_acquisition_to_complete(self) -> None:
        """See `SpectrumDigitiserCard.wait_for_acquisition_to_complete()`. This mock implementation blocks until a mock
        acquisition has been completed (i.e. the acquisition thread has shut down) or the request has timed out
        according to the `self.timeout_ms attribute`."""
        if self._acquisition_thread is not None:
            self._acquisition_thread.join(timeout=1e-3 * self.timeout_in_ms)
            if self._acquisition_thread.is_alive():
                logger.warning("A timeout occurred while waiting for mock acquisition to complete.")
        else:
            logger.warning("No acquisition in progress. Wait for acquisition to complete has no effect")


class MockSpectrumAWGCard(MockAbstractSpectrumAWG, MockAbstractSpectrumCard, SpectrumAWGCard):
    """A mock AWG card."""

    def __init__(
        self,
        device_number: int,
        model: ModelNumber,
        num_modules: int,
        num_channels_per_module: int,
        card_features: Optional[list[CardFeature]] = None,
        advanced_card_features: Optional[list[AdvancedCardFeature]] = None,
    ) -> None:
        """
        Args:
            device_number (int): The index of the mock device to create. Used to create a name for the device which is
                used internally.
            model (ModelNumber): The model of card to mock.
            num_modules (int): The number of internal modules to assign the mock card. Default 2. On real hardware, this
                is read from the device so does not need to be set. See the Spectrum documentation to work out how many
                modules your hardware has.
            num_channels_per_module (int): The number of channels per module. Default 4 (so 8 channels in total). On
                real hardware, this is read from the device so does not need to be set.
            card_features (list[CardFeature]): List of available features of the mock device
            advanced_card_features (list[AdvancedCardFeature]): List of available advanced features of the mock device
        """
        super().__init__(
            card_type=CardType.SPCM_TYPE_AO,
            device_number=device_number,
            model=model,
            num_modules=num_modules,
            num_channels_per_module=num_channels_per_module,
            card_features=card_features if card_features is not None else [],
            advanced_card_features=advanced_card_features if advanced_card_features is not None else [],
        )
        self._connect(self._visa_string)

    def define_transfer_buffer(self, buffer: Optional[Sequence[TransferBuffer]] = None) -> None:
        """Create or provide a `TransferBuffer` object for transferring samples from the device.

        See SpectrumAWGCard.define_transfer_buffer(). This mock implementation is identical apart from that it
        does not write to any hardware device."""
        if buffer is None:
            raise ValueError(
                "You must provide a preconfigured buffer for transferring samples to an AWG because the"
                "buffer size cannot be inferred."
            )
        self._transfer_buffer = buffer[0]


class MockSpectrumDigitiserStarHub(MockAbstractSpectrumStarHub, SpectrumDigitiserStarHub):
    """A mock spectrum StarHub, for testing software written to use the `SpectrumStarHub` class.

    Overrides methods of `SpectrumStarHub` and `AbstractSpectrumDigitiser` that communicate with hardware with mocked
    implementations allowing software to be tested without Spectrum hardware connected or drivers installed, e.g. during
    CI."""

    def __init__(self, **kwargs: Any):
        """
        Args:
            child_cards (Sequence[`MockSpectrumDigitiserCard`]): A list of `MockSpectrumDigitiserCard` objects defining the
                properties of the child cards located within the mock hub.
            master_card_index (int): The position within child_cards where the master card (the card which controls the
                clock) is located.
        """
        super().__init__(param_dict=None, **kwargs)
        self._visa_string = "/mock" + self._visa_string
        self._connect(self._visa_string)
        self._acquisition_mode = self.acquisition_mode

    def start(self) -> None:
        """Start a mock acquisition

        See `AbstractSpectrumDevice.start()`. With a hardware device, StarHub's only need to be sent a single
        instruction to start acquisition, which they automatically relay to their child cards - hence why
        `start` is implemented in `AbstractSpectrumDevice` (base class to both `SpectrumDigitiserCard` and
        `SpectrumStarHub`) rather than in `SpectrumStarHub`. In this mock `implementation`, each card's acquisition is
        started individually.

        """
        for card in self._child_cards:
            card.start()

    def stop(self) -> None:
        """Stop a mock acquisition

        See `AbstractSpectrumDevice.stop_acquisition`. With a hardware device, StarHub's only need to be sent a single
        instruction to stop acquisition, which they automatically relay to their child cards - hence why
        `stop_acquisition()` is implemented in `AbstractSpectrumDevice` (base class to both `SpectrumDigitiserCard` and
        `SpectrumStarHub`) rather than in `SpectrumStarHub`. In this mock implementation, each card's acquisition is
        stopped individually.

        """
        for card in self._child_cards:
            card.stop()
