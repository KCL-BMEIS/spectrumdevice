"""Provides a concrete class for controlling an individual Spectrum digitiser device."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.
import datetime
import logging
from functools import reduce
from operator import or_
from typing import List, Optional, Tuple, Sequence

from numpy import mod, float_
from numpy.typing import NDArray

from spectrumdevice.devices.spectrum_timestamper import Timestamper
from spectrumdevice.settings.card_dependent_properties import get_memsize_step_size
from spectrumdevice.settings.device_modes import AcquisitionMode, ClockMode
from spectrumdevice.spectrum_wrapper import destroy_handle
from spectrumdevice.settings import (
    CARD_STATUS_TYPE,
    CardType,
    AvailableIOModes,
    TriggerSource,
    ExternalTriggerMode,
    CardFeature,
    AdvancedCardFeature,
    TransferBuffer,
    CardToPCDataTransferBuffer,
    SpectrumRegisterLength,
)
from spectrumdevice.settings.status import decode_status
from spectrumdevice.settings.io_lines import decode_available_io_modes
from spectrumdevice.settings.triggering import (
    EXTERNAL_TRIGGER_MODE_COMMANDS,
    EXTERNAL_TRIGGER_LEVEL_COMMANDS,
    decode_trigger_sources,
    EXTERNAL_TRIGGER_PULSE_WIDTH_COMMANDS,
)
from spectrumdevice.settings.card_features import decode_card_features, decode_advanced_card_features
from spectrumdevice.settings.transfer_buffer import set_transfer_buffer
from spectrumdevice.devices.spectrum_channel import SpectrumChannel
from spectrumdevice.devices.spectrum_device import SpectrumDevice
from spectrumdevice.exceptions import (
    SpectrumInvalidNumberOfEnabledChannels,
    SpectrumNoTransferBufferDefined,
    SpectrumExternalTriggerNotEnabled,
    SpectrumTriggerOperationNotImplemented,
)
from spectrum_gmbh.regs import (
    M2CMD_CARD_WAITREADY,
    SPC_M2CMD,
    M2CMD_DATA_STARTDMA,
    M2CMD_DATA_STOPDMA,
    SPC_M2STATUS,
    SPC_TRIG_ORMASK,
    SPC_TRIG_ANDMASK,
    SPC_CHENABLE,
    SPC_MIINST_MODULES,
    SPC_MIINST_CHPERMODULE,
    SPC_MEMSIZE,
    SPC_POSTTRIGGER,
    SPC_CARDMODE,
    SPC_TIMEOUT,
    SPC_CLOCKMODE,
    SPC_SAMPLERATE,
    M2CMD_DATA_WAITDMA,
    SPCM_X0_AVAILMODES,
    SPC_PCIFEATURES,
    SPC_PCIEXTFEATURES,
    SPCM_X1_AVAILMODES,
    SPCM_X2_AVAILMODES,
    SPCM_X3_AVAILMODES,
    SPC_DATA_AVAIL_USER_LEN,
    SPC_DATA_AVAIL_CARD_LEN,
    SPC_SEGMENTSIZE,
    SPC_PCITYP,
)

logger = logging.getLogger(__name__)


class SpectrumCard(SpectrumDevice):
    """Class for controlling individual Spectrum digitiser cards."""

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
        self._card_type = CardType(self.read_spectrum_device_register(SPC_PCITYP))
        self._trigger_sources: List[TriggerSource] = []
        self._channels = self._init_channels()
        self._enabled_channels: List[int] = [0]
        self._transfer_buffer: Optional[TransferBuffer] = None
        self.apply_channel_enabling()
        self._acquisition_mode = self.acquisition_mode
        self._timestamper: Optional[Timestamper] = None

    def enable_timestamping(self) -> None:
        self._timestamper = Timestamper(self, self._handle)

    def reconnect(self) -> None:
        """Reconnect to the card after disconnect() has been called."""
        self._connect(self._visa_string)

    @property
    def status(self) -> CARD_STATUS_TYPE:
        """Read the current acquisition status of the card.
        Returns:
            Statuses (`List[StatusCode]`): A list of `StatusCode` Enums describing the current acquisition status of the
                card. See `StatusCode` (and the Spectrum documentation) for the list off possible acquisition
                statuses.
        """
        return decode_status(self.read_spectrum_device_register(SPC_M2STATUS))

    def wait_for_acquisition_to_complete(self) -> None:
        """Blocks until the current acquisition has finished, or the timeout is reached.

        In Standard Single mode (SPC_REC_STD_SINGLE), this should be called after `start_acquisition()`. Once the call
            to `wait_for_acquisition_to_complete()` returns, the newly acquired samples are in the on_device buffer and
            ready for transfer to the `TransferBuffer` using `start_transfer()`.

        In FIFO mode (SPC_REC_FIFO_MULTI), the card will continue to acquire samples until
            `stop_acquisition()` is called, so `wait_for_acquisition_to_complete()` should not be used.

        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_WAITREADY)

    def start_transfer(self) -> None:
        """Transfer acquired waveforms from the on-device buffer to the `TransferBuffer`.

        Requires that a `TransferBuffer` has been defined (see `define_transfer_buffer()`).

        In Standard Single mode (SPC_REC_STD_SINGLE), `start_transfer()` should be called after each acquisition has
        completed.

        In FIFO mode (SPC_REC_FIFO_MULTI), `start_transfer()` should be called immediately after `start_acquisition()`
        has been called, so that the waveform data can be continuously streamed into the transfer buffer as it is
        acquired.
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_DATA_STARTDMA)

    def stop_transfer(self) -> None:
        """Stop the transfer of samples from the on-device buffer to the `TransferBuffer`.

        Transfer is usually stopped automatically when an acquisition or stream of acquisitions completes, so this
        method is rarely required. It may invalidate transferred samples.

        In Standard Single mode (SPC_REC_STD_SINGLE), transfer will automatically stop once all acquired samples have
        been transferred, so `stop_transfer()` should not be used. Instead, call `wait_for_transfer_to_complete()` after
        `start_transfer()`.

        In FIFO mode (SPC_REC_FIFO_MULTI), samples are transferred continuously during acquisition,
        and transfer will automatically stop when `stop_acquisition()` is called as there will be no more
        samples to transfer, so `stop_transfer()` should not be used.

        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_DATA_STOPDMA)

    def wait_for_transfer_to_complete(self) -> None:
        """Blocks until the currently active transfer of samples from the on-device buffers to the TransferBuffer is
        complete.

        Used in Standard Single mode (SPC_REC_STD_SINGLE) after starting a transfer. Once the method returns, all
        acquired waveforms have been transferred from the on_device buffer to the `TransferBuffer` and can be read using
        the `get_waveforms()` method.

        Not required in FIFO mode (SPC_REC_FIFO_MULTI) because samples are continuously streamed until
        `stop_acquisition()` is called.
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_DATA_WAITDMA)

    @property
    def transfer_buffers(self) -> List[TransferBuffer]:
        """Return the `TransferBuffer` object containing the latest transferred samples.

        Returns:
            buffer (List[`TransferBuffer`]): A length-1 list containing the `TransferBuffer` object. The samples within
                the `TransferBuffer` can be accessed using its own interface, but the samples are stored as a 1D array,
                with the samples of each channel interleaved. It is more convenient to read waveform data using the
                `get_waveforms()` method.

        """
        if self._transfer_buffer is not None:
            return [self._transfer_buffer]
        else:
            raise SpectrumNoTransferBufferDefined("Cannot find TransferBuffer.")

    def define_transfer_buffer(self, buffer: Optional[List[CardToPCDataTransferBuffer]] = None) -> None:
        """Create or provide a `CardToPCDataTransferBuffer` object for receiving acquired samples from the device.

        If no buffer is provided, one will be created with the correct size and a board_memory_offset_bytes of 0. A
        seperate buffer for transfering Timestamps will also be created using the Timestamper class.

        Args:
            buffer (Optional[List[`CardToPCDataTransferBuffer`]]): A length-1 list containing a pre-constructed
                `CardToPCDataTransferBuffer`  The size of the buffer should be chosen according to the current number of
                active channels and the acquisition length.
        """
        if buffer:
            self._transfer_buffer = buffer[0]
        else:
            self._transfer_buffer = CardToPCDataTransferBuffer(
                self.acquisition_length_in_samples * len(self.enabled_channels)
            )
        set_transfer_buffer(self._handle, self._transfer_buffer)

    def get_waveforms(self) -> List[NDArray[float_]]:
        """Get a list of the most recently transferred waveforms, in channel order.

        This method copies and reshapes the samples in the `TransferBuffer` into a list of 1D NumPy arrays (waveforms)
        and returns the list.

        In Standard Single mode (SPC_REC_STD_SINGLE), `get_waveforms()` should be called after
        `wait_for_transfer_to_complete()` has returned.

        In FIFO mode (SPC_REC_FIFO_MULTI), while the card is continuously acquiring samples and transferring them to the
        `TransferBuffer`, this method should be called in a loop . The method will block until each new transfer is
        received, so the loop will run at the same rate as the acquisition (in SPC_REC_FIFO_MULTI mode, for example,
        this would the rate at which your trigger source was running).

        Returns:
            waveforms (List[NDArray[float_]]): A list of 1D NumPy arrays, one for each channel enabled for the
                acquisition, ordered by channel number.

        """
        num_available_bytes = 0
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            self.wait_for_transfer_to_complete()
            num_available_bytes = self.read_spectrum_device_register(SPC_DATA_AVAIL_USER_LEN)

        if self._transfer_buffer is not None:
            num_expected_bytes_per_frame = self._transfer_buffer.data_array_length_in_bytes
            if num_available_bytes > num_expected_bytes_per_frame:
                num_available_bytes = num_expected_bytes_per_frame
        else:
            raise SpectrumNoTransferBufferDefined("Cannot find a samples transfer buffer")

        waveforms_in_columns = (
            self.transfer_buffers[0]
            .copy_contents()
            .reshape((self.acquisition_length_in_samples, len(self.enabled_channels)))
        )
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            self.write_to_spectrum_device_register(SPC_DATA_AVAIL_CARD_LEN, num_available_bytes)

        voltage_waveforms = [
            ch.convert_raw_waveform_to_voltage_waveform(waveform)
            for ch, waveform in zip(self.channels, waveforms_in_columns.T)
        ]

        return voltage_waveforms

    def get_timestamp(self) -> Optional[datetime.datetime]:
        """Get timestamp for the last acquisition"""
        if self._timestamper is not None:
            return self._timestamper.get_timestamp()
        else:
            return None

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
        if isinstance(other, SpectrumCard):
            return self._handle == other._handle
        else:
            raise NotImplementedError()

    @property
    def channels(self) -> Sequence[SpectrumChannel]:
        """A tuple containing the channels that belong to the digitiser card.

        Properties of the individual channels (e.g. vertical range) can be set by calling the methods of the
            returned objects directly. See `SpectrumChannel` for more information.

        Returns:
            channels (Sequence[`SpectrumChannel`]): A tuple of `SpectrumChannel` objects.
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
        """The signal level (mV) needed to trigger an acquisition using an external trigger source. An external
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
        """Change the signal level (mV) needed to trigger an acquisition using an external trigger source. An external
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
        """The pulse width (in samples) needed to trigger an acquisition using an external trigger source, if
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
        """Change the pulse width (samples) needed to trigger an acquisition using an external trigger source if
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

    def _init_channels(self) -> Sequence[SpectrumChannel]:
        num_modules = self.read_spectrum_device_register(SPC_MIINST_MODULES)
        num_channels_per_module = self.read_spectrum_device_register(SPC_MIINST_CHPERMODULE)
        total_channels = num_modules * num_channels_per_module
        return tuple([SpectrumChannel(n, self) for n in range(total_channels)])

    @property
    def acquisition_length_in_samples(self) -> int:
        """The current recording length (per channel) in samples.

        Returns:
            length_in_samples (int): The current recording length ('acquisition length') in samples."""
        return self.read_spectrum_device_register(SPC_MEMSIZE)

    def set_acquisition_length_in_samples(self, length_in_samples: int) -> None:
        """Change the recording length (per channel). In FIFO mode, it will be quantised according to the step size
          allowed by the connected card type.

        Args:
            length_in_samples (int): The desired recording length ('acquisition length'), in samples.
        """
        length_in_samples = self._coerce_num_samples_if_fifo(length_in_samples)
        self.write_to_spectrum_device_register(SPC_SEGMENTSIZE, length_in_samples)
        self.write_to_spectrum_device_register(SPC_MEMSIZE, length_in_samples)

    @property
    def post_trigger_length_in_samples(self) -> int:
        """The number of samples of the recording that will contain data received after the trigger event.

        Returns:
            length_in_samples (int): The currently set post trigger length in samples.
        """
        return self.read_spectrum_device_register(SPC_POSTTRIGGER)

    def set_post_trigger_length_in_samples(self, length_in_samples: int) -> None:
        """Change the number of samples of the recording that will contain data received after the trigger event.
        In FIFO mode, this will be quantised according to the minimum step size allowed by the connected card.

        Args:
            length_in_samples (int): The desired post trigger length in samples."""
        length_in_samples = self._coerce_num_samples_if_fifo(length_in_samples)
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            if (self.acquisition_length_in_samples - length_in_samples) < get_memsize_step_size(self._card_type):
                logger.warning(
                    "FIFO mode: coercing post trigger length to maximum allowed value (step-size samples less than "
                    "the acquisition length)."
                )
                length_in_samples = self.acquisition_length_in_samples - get_memsize_step_size(self._card_type)
        self.write_to_spectrum_device_register(SPC_POSTTRIGGER, length_in_samples)

    def _coerce_num_samples_if_fifo(self, value: int) -> int:
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            if value != mod(value, get_memsize_step_size(self._card_type)):
                logger.warning(
                    f"FIFO mode: coercing length to nearest {get_memsize_step_size(self._card_type)}" f" samples"
                )
                value = int(value - mod(value, get_memsize_step_size(self._card_type)))
        return value

    @property
    def acquisition_mode(self) -> AcquisitionMode:
        """The currently enabled card mode. Will raise an exception if the current mode is not supported by
        `spectrumdevice`.

        Returns:
            mode (`AcquisitionMode`): The currently enabled card acquisition mode."""
        return AcquisitionMode(self.read_spectrum_device_register(SPC_CARDMODE))

    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        """Change the currently enabled card mode. See `AcquisitionMode` and the Spectrum documentation
        for the available modes.

        Args:
            mode (`AcquisitionMode`): The desired acquisition mode."""
        self.write_to_spectrum_device_register(SPC_CARDMODE, mode.value)

    @property
    def timeout_in_ms(self) -> int:
        """The time for which the card will wait for a trigger to tbe received after an acquisition has started
        before returning an error.

        Returns:
            timeout_in_ms (in)t: The currently set acquisition timeout in ms.
        """
        return self.read_spectrum_device_register(SPC_TIMEOUT)

    def set_timeout_in_ms(self, timeout_in_ms: int) -> None:
        """Change the time for which the card will wait for a trigger to tbe received after an acquisition has started
        before returning an error.

        Args:
            timeout_in_ms (int): The desired acquisition timeout in ms.
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
        """The rate at which samples will be acquired during an acquisition, in Hz.

        Returns:
            rate (int): The currently set sample rate in Hz.
        """
        return self.read_spectrum_device_register(SPC_SAMPLERATE, SpectrumRegisterLength.SIXTY_FOUR)

    def set_sample_rate_in_hz(self, rate: int) -> None:
        """Change the rate at which samples will be acquired during an acquisition, in Hz.
        Args:
            rate (int): The desired sample rate in Hz.
        """
        self.write_to_spectrum_device_register(SPC_SAMPLERATE, rate, SpectrumRegisterLength.SIXTY_FOUR)

    def __str__(self) -> str:
        return f"Card {self._visa_string}"


def _create_visa_string_from_ip(ip_address: str, instrument_number: int) -> str:
    return f"TCPIP[0]::{ip_address}::inst{instrument_number}::INSTR"
