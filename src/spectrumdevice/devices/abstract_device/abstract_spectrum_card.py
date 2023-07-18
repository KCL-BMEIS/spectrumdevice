"""Provides a partially implemented abstract superclass for all individual Spectrum cards (as opposed to Spectrum Star
Hubs, which are aggregates of multiple cards)."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

import logging
from abc import ABC, abstractmethod
from functools import reduce
from operator import or_
from typing import List, Optional, Sequence, Tuple

from spectrum_gmbh.regs import (
    M2CMD_DATA_STARTDMA,
    M2CMD_DATA_STOPDMA,
    M2CMD_DATA_WAITDMA,
    SPCM_X0_AVAILMODES,
    SPCM_X1_AVAILMODES,
    SPCM_X2_AVAILMODES,
    SPCM_X3_AVAILMODES,
    SPC_CHENABLE,
    SPC_CLOCKMODE,
    SPC_FNCTYPE,
    SPC_M2CMD,
    SPC_M2STATUS,
    SPC_PCIEXTFEATURES,
    SPC_PCIFEATURES,
    SPC_PCITYP,
    SPC_SAMPLERATE,
    SPC_TIMEOUT,
    SPC_TRIG_ANDMASK,
    SPC_TRIG_ORMASK,
)
from spectrumdevice.devices.abstract_device.abstract_spectrum_device import AbstractSpectrumDevice
from spectrumdevice.devices.abstract_device.device_interface import SpectrumChannelInterface
from spectrumdevice.exceptions import (
    SpectrumExternalTriggerNotEnabled,
    SpectrumInvalidNumberOfEnabledChannels,
    SpectrumNoTransferBufferDefined,
    SpectrumTriggerOperationNotImplemented,
)
from spectrumdevice.settings import (
    AdvancedCardFeature,
    AvailableIOModes,
    CardFeature,
    ModelNumber,
    DEVICE_STATUS_TYPE,
    ExternalTriggerMode,
    SpectrumRegisterLength,
    TransferBuffer,
    TriggerSource,
)
from spectrumdevice.settings.card_dependent_properties import CardType
from spectrumdevice.settings.card_features import decode_advanced_card_features, decode_card_features
from spectrumdevice.settings.device_modes import ClockMode
from spectrumdevice.settings.io_lines import decode_available_io_modes
from spectrumdevice.settings.status import decode_status
from spectrumdevice.settings.triggering import (
    EXTERNAL_TRIGGER_LEVEL_COMMANDS,
    EXTERNAL_TRIGGER_MODE_COMMANDS,
    EXTERNAL_TRIGGER_PULSE_WIDTH_COMMANDS,
    decode_trigger_sources,
)
from spectrumdevice.spectrum_wrapper import destroy_handle

logger = logging.getLogger(__name__)


class AbstractSpectrumCard(AbstractSpectrumDevice, ABC):
    """Abstract superclass implementing methods common to all individual "card" devices (as opposed to "hub" devices)."""

    def __init__(self, device_number: int = 0, ip_address: Optional[str] = None):
        """
        Args:
            device_number (int): Index of the card to control. If only one card is present, set to 0.
            ip_address (Optional[str]): If connecting to a networked card, provide the IP address here as a string.

        """
        if ip_address is not None:
            self._visa_string = _create_visa_string_from_ip(ip_address, device_number)
        else:
            self._visa_string = f"/dev/spcm{device_number}"
        self._connect(self._visa_string)
        self._model_number = ModelNumber(self.read_spectrum_device_register(SPC_PCITYP))
        self._trigger_sources: List[TriggerSource] = []
        self._channels = self._init_channels()
        self._enabled_channels: List[int] = [0]
        self._transfer_buffer: Optional[TransferBuffer] = None
        self.apply_channel_enabling()

    @property
    def model_number(self) -> ModelNumber:
        return self._model_number

    def reconnect(self) -> None:
        """Reconnect to the card after disconnect() has been called."""
        self._connect(self._visa_string)

    @property
    def status(self) -> DEVICE_STATUS_TYPE:
        """Read the current status of the card.
        Returns:
            Statuses (`List[List[StatusCode]]`): A length-1 list containing a list of `StatusCode` Enums describing the
            current acquisition status of the card. See `StatusCode` (and the Spectrum documentation) for the list off
            possible acquisition statuses.
        """
        return [decode_status(self.read_spectrum_device_register(SPC_M2STATUS))]

    def start_transfer(self) -> None:
        """Transfer between the on-device buffer and the `TransferBuffer`.

        Requires that a `TransferBuffer` has been defined (see `define_transfer_buffer()`).

        For digitisers in Standard Single mode (SPC_REC_STD_SINGLE), `start_transfer()` should be called after each
        acquisition has completed to transfer the acquired waveforms from the device to the `TransferBuffer`.

        For digitisers in FIFO mode (SPC_REC_FIFO_MULTI), `start_transfer()` should be called immediately after
        `start()` has been called, so that the waveform data can be continuously streamed into the transfer buffer as it
        is acquired.
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_DATA_STARTDMA)

    def stop_transfer(self) -> None:
        """Stop the transfer of data between the on-device buffer and the `TransferBuffer`.

        Transfer is usually stopped automatically when an acquisition or stream of acquisitions completes, so this
        method is rarely required. It may invalidate transferred samples.

        For digitisers in Standard Single mode (SPC_REC_STD_SINGLE), transfer will automatically stop once all acquired
        samples have been transferred, so `stop_transfer()` should not be used. Instead, call
        `wait_for_transfer_to_complete()` after `start_transfer()`.

        For digitisers in FIFO mode (SPC_REC_FIFO_MULTI), samples are transferred continuously during acquisition,
        and transfer will automatically stop when `stop()` is called as there will be no more
        samples to transfer, so `stop_transfer()` should not be used.
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_DATA_STOPDMA)

    def wait_for_transfer_chunk_to_complete(self) -> None:
        """Blocks until the currently active transfer between the on-device buffer and the TransferBuffer is
        complete. This will be when there at least TransferBuffer.notify_size_in_pages pages available in the buffer.

        For digitisers in Standard Single mode (SPC_REC_STD_SINGLE), use after starting a transfer. Once the method
        returns, all acquired waveforms have been transferred from the on-device buffer to the `TransferBuffer` and can
        be read using the `get_waveforms()` method.

        For digitisers in FIFO mode (SPC_REC_FIFO_MULTI) this method is internally used by get_waveforms().
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_DATA_WAITDMA)

    @property
    def transfer_buffers(self) -> List[TransferBuffer]:
        """Return the `TransferBuffer` configured for transferring data between the card and the software.

        Returns:
            buffer (List[`TransferBuffer`]): A length-1 list containing the `TransferBuffer` object. Any data within
                the `TransferBuffer` can be accessed using its own interface, but the samples are stored as a 1D array,
                with the samples of each channel interleaved as per the Spectrum user manual. For digitisers, it is more
                convenient to read waveform data using the `get_waveforms()` method.
        """
        if self._transfer_buffer is not None:
            return [self._transfer_buffer]
        else:
            raise SpectrumNoTransferBufferDefined("Cannot find TransferBuffer.")

    def disconnect(self) -> None:
        """Terminate the connection to the card."""
        if self.connected:
            destroy_handle(self._handle)
            self._connected = False

    @property
    def connected(self) -> bool:
        """Returns True if a card is currently connected, False if not."""
        return self._connected

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self._handle == other._handle
        else:
            raise NotImplementedError(f"Cannot compare {self.__class__} with {other.__class__}")

    @property
    def channels(self) -> Sequence[SpectrumChannelInterface]:
        """A tuple containing the channels that belong to the card.

        Properties of the individual channels can be set by calling the methods of the
            returned objects directly. See `SpectrumDigitiserChannel` and `SpectrumAWGChannel` for more information.

        Returns:
            channels (Sequence[`SpectrumChannelInterface`]): A tuple of objects conforming to the
            `SpectrumChannelInterface` interface.
        """
        return self._channels

    @property
    def enabled_channels(self) -> List[int]:
        """The indices of the currently enabled channels.
        Returns:
            enabled_channels (List[int]): The indices of the currently enabled channels.
        """
        return self._enabled_channels

    def set_enabled_channels(self, channels_nums: List[int]) -> None:
        """Change which channels are enabled.

        Args:
            channels_nums (List[int]): The integer channel indices to enable.
        """
        if len(channels_nums) in [1, 2, 4, 8]:
            self._enabled_channels = channels_nums
            self.apply_channel_enabling()
        else:
            raise SpectrumInvalidNumberOfEnabledChannels(f"{len(channels_nums)} cannot be enabled at once.")

    @property
    def trigger_sources(self) -> List[TriggerSource]:
        """The currently enabled trigger sources

        Returns:
            sources (List[`TriggerSource`]): A list of TriggerSources.
        """
        or_of_sources = self.read_spectrum_device_register(SPC_TRIG_ORMASK)
        self._trigger_sources = decode_trigger_sources(or_of_sources)
        return self._trigger_sources

    def set_trigger_sources(self, sources: List[TriggerSource]) -> None:
        """Change the enabled trigger sources.

        Args:
            sources (List[`TriggerSource`]): The TriggerSources to enable.
        """
        self._trigger_sources = sources
        or_of_sources = reduce(or_, [s.value for s in sources])
        self.write_to_spectrum_device_register(SPC_TRIG_ORMASK, or_of_sources)
        self.write_to_spectrum_device_register(SPC_TRIG_ANDMASK, 0)

    @property
    def external_trigger_mode(self) -> ExternalTriggerMode:
        """The currently enabled external trigger mode. An external trigger source must be enabled.

        Returns:
            sources (`ExternalTriggerMode`): The currently enabled `ExternalTriggerMode`."""
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot get external trigger mode.")
        else:
            first_trig_source = self._active_external_triggers[0]
            try:
                return ExternalTriggerMode(
                    self.read_spectrum_device_register(EXTERNAL_TRIGGER_MODE_COMMANDS[first_trig_source.value])
                )
            except KeyError:
                raise SpectrumTriggerOperationNotImplemented(f"Cannot get trigger mode of {first_trig_source.name}.")

    def set_external_trigger_mode(self, mode: ExternalTriggerMode) -> None:
        """Change the currently enabled trigger mode. An external trigger source must be enabled.

        Args:
            mode (`ExternalTriggerMode`): The `ExternalTriggerMode` to apply.
        """
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot set external trigger mode.")
        else:
            for trigger_source in self._active_external_triggers:
                try:
                    self.write_to_spectrum_device_register(
                        EXTERNAL_TRIGGER_MODE_COMMANDS[trigger_source.value], mode.value
                    )
                except KeyError:
                    raise SpectrumTriggerOperationNotImplemented(f"Cannot set trigger mode of {trigger_source.name}.")

    @property
    def _active_external_triggers(self) -> List[TriggerSource]:
        return [
            TriggerSource(val)
            for val in list(
                set(EXTERNAL_TRIGGER_MODE_COMMANDS.keys()) & set([source.value for source in self._trigger_sources])
            )
        ]

    @property
    def external_trigger_level_in_mv(self) -> int:
        """The signal level (mV) needed to trigger an event using an external trigger source. An external
        trigger source must be enabled.

        Returns:
            level (int): The currently set trigger level in mV.
        """
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot get external trigger level.")
        else:
            first_trig_source = self._active_external_triggers[0]
            try:
                return self.read_spectrum_device_register(EXTERNAL_TRIGGER_LEVEL_COMMANDS[first_trig_source.value])
            except KeyError:
                raise SpectrumTriggerOperationNotImplemented(f"Cannot get trigger level of {first_trig_source.name}.")

    def set_external_trigger_level_in_mv(self, level: int) -> None:
        """Change the signal level (mV) needed to trigger an event using an external trigger source. An external
        trigger source must be enabled.

        Args:
            level (int): The trigger level to set in mV.
        """
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot set external trigger level.")
        else:
            for trigger_source in self._active_external_triggers:
                try:
                    self.write_to_spectrum_device_register(EXTERNAL_TRIGGER_LEVEL_COMMANDS[trigger_source.value], level)
                except KeyError:
                    raise SpectrumTriggerOperationNotImplemented(f"Cannot set trigger level of {trigger_source.name}.")

    @property
    def external_trigger_pulse_width_in_samples(self) -> int:
        """The pulse width (in samples) needed to trigger an event using an external trigger source, if
        SPC_TM_PW_SMALLER or SPC_TM_PW_GREATER `ExternalTriggerMode` is selected. An external trigger source must be
        enabled.

        Returns:
            width (int): The current trigger pulse width in samples.
        """
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot get external trigger pulse width.")
        else:
            first_trig_source = self._active_external_triggers[0]
            try:
                return self.read_spectrum_device_register(
                    EXTERNAL_TRIGGER_PULSE_WIDTH_COMMANDS[first_trig_source.value]
                )
            except KeyError:
                raise SpectrumTriggerOperationNotImplemented(f"Cannot get pulse width of {first_trig_source.name}.")

    def set_external_trigger_pulse_width_in_samples(self, width: int) -> None:
        """Change the pulse width (samples) needed to trigger an event using an external trigger source if
        SPC_TM_PW_SMALLER or SPC_TM_PW_GREATER `ExternalTriggerMode` is selected. An external trigger source must be
        enabled.

        Args:
            width (int): The trigger pulse width to set, in samples."""
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot set external trigger pulse width.")
        else:
            for trigger_source in self._active_external_triggers:
                try:
                    self.write_to_spectrum_device_register(
                        EXTERNAL_TRIGGER_PULSE_WIDTH_COMMANDS[trigger_source.value], width
                    )
                except KeyError:
                    raise SpectrumTriggerOperationNotImplemented(f"Cannot set pulse width of {trigger_source.name}.")

    def apply_channel_enabling(self) -> None:
        """Apply the enabled channels chosen using set_enable_channels(). This happens automatically and does not
        usually need to be called."""
        enabled_channel_spectrum_values = [self.channels[i].name.value for i in self._enabled_channels]
        if len(enabled_channel_spectrum_values) in [1, 2, 4, 8]:
            bitwise_or_of_enabled_channels = reduce(or_, enabled_channel_spectrum_values)
            self.write_to_spectrum_device_register(SPC_CHENABLE, bitwise_or_of_enabled_channels)
        else:
            raise SpectrumInvalidNumberOfEnabledChannels(
                f"Cannot enable {len(enabled_channel_spectrum_values)} " f"channels on one card."
            )

    @abstractmethod
    def _init_channels(self) -> Sequence[SpectrumChannelInterface]:
        raise NotImplementedError()

    @property
    def timeout_in_ms(self) -> int:
        """The time for which the card will wait for a trigger to be received after the device has been started
        before returning an error.

        Returns:
            timeout_in_ms (in)t: The currently set timeout in ms.
        """
        return self.read_spectrum_device_register(SPC_TIMEOUT)

    def set_timeout_in_ms(self, timeout_in_ms: int) -> None:
        """Change the time for which the card will wait for a trigger to tbe received after the device has started
        before returning an error.

        Args:
            timeout_in_ms (int): The desired timeout in ms.
        """
        self.write_to_spectrum_device_register(SPC_TIMEOUT, timeout_in_ms)

    @property
    def clock_mode(self) -> ClockMode:
        """The currently enabled clock mode.

        Returns:
            mode (`ClockMode`): The currently set clock mode.
        """
        return ClockMode(self.read_spectrum_device_register(SPC_CLOCKMODE))

    def set_clock_mode(self, mode: ClockMode) -> None:
        """Change the clock mode. See `ClockMode` and the Spectrum documentation for available modes.

        Args:
            mode (`ClockMode`): The desired clock mode.
        """
        self.write_to_spectrum_device_register(SPC_CLOCKMODE, mode.value)

    @property
    def available_io_modes(self) -> AvailableIOModes:
        """For each multipurpose IO line on the card, read the available modes. See IOLineMode and the Spectrum
        Documentation for all possible available modes and their meanings.

        Returns:
            modes (`AvailableIOModes`): An `AvailableIOModes` dataclass containing the modes for each IO line."""
        return AvailableIOModes(
            X0=decode_available_io_modes(self.read_spectrum_device_register(SPCM_X0_AVAILMODES)),
            X1=decode_available_io_modes(self.read_spectrum_device_register(SPCM_X1_AVAILMODES)),
            X2=decode_available_io_modes(self.read_spectrum_device_register(SPCM_X2_AVAILMODES)),
            X3=decode_available_io_modes(self.read_spectrum_device_register(SPCM_X3_AVAILMODES)),
        )

    @property
    def feature_list(self) -> List[Tuple[List[CardFeature], List[AdvancedCardFeature]]]:
        """Get a list of the features of the card. See `CardFeature`, `AdvancedCardFeature` and the Spectrum
        documentation for more information.

        Returns:
            features (List[Tuple[List[`CardFeature`], List[`AdvancedCardFeature`]]]): A tuple of two lists - of features
                and advanced features respectively - wrapped in a list.
        """
        normal_features = decode_card_features(self.read_spectrum_device_register(SPC_PCIFEATURES))
        advanced_features = decode_advanced_card_features(self.read_spectrum_device_register(SPC_PCIEXTFEATURES))
        return [(normal_features, advanced_features)]

    @property
    def sample_rate_in_hz(self) -> int:
        """The rate at which samples will be acquired or generated, in Hz.

        Returns:
            rate (int): The currently set sample rate in Hz.
        """
        return self.read_spectrum_device_register(SPC_SAMPLERATE, SpectrumRegisterLength.SIXTY_FOUR)

    def set_sample_rate_in_hz(self, rate: int) -> None:
        """Change the rate at which samples will be acquired or generated, in Hz.
        Args:
            rate (int): The desired sample rate in Hz.
        """
        self.write_to_spectrum_device_register(SPC_SAMPLERATE, rate, SpectrumRegisterLength.SIXTY_FOUR)

    def __str__(self) -> str:
        return f"Card {self._visa_string} (model {self.model_number.name})."

    @property
    def type(self) -> CardType:
        return CardType(self.read_spectrum_device_register(SPC_FNCTYPE))


def _create_visa_string_from_ip(ip_address: str, instrument_number: int) -> str:
    return f"TCPIP[0]::{ip_address}::inst{instrument_number}::INSTR"
