from copy import copy
from functools import reduce
from operator import or_
from typing import List, Optional, Tuple

from numpy import ndarray, mod

from pyspecde.spectrum_api_wrapper import (
    destroy_handle,
    AcquisitionMode,
    ClockMode,
)
from pyspecde.spectrum_api_wrapper.status import CARD_STATUS_TYPE, decode_status
from pyspecde.spectrum_api_wrapper.io_lines import decode_available_io_modes, AvailableIOModes
from pyspecde.spectrum_api_wrapper.triggering import (
    TriggerSource,
    ExternalTriggerMode,
    EXTERNAL_TRIGGER_MODE_COMMANDS,
    EXTERNAL_TRIGGER_LEVEL_COMMANDS,
    decode_trigger_sources,
)
from pyspecde.spectrum_api_wrapper.card_features import (
    CardFeature,
    decode_card_features,
    AdvancedCardFeature,
    decode_advanced_card_features,
)
from pyspecde.spectrum_api_wrapper.transfer_buffer import (
    TransferBuffer,
    set_transfer_buffer,
    CardToPCDataTransferBuffer,
)
from pyspecde.hardware_model.spectrum_channel import SpectrumChannel
from pyspecde.hardware_model.spectrum_device import SpectrumDevice
from pyspecde.exceptions import (
    SpectrumInvalidNumberOfEnabledChannels,
    SpectrumNoTransferBufferDefined,
    SpectrumExternalTriggerNotEnabled,
    SpectrumTriggerOperationNotImplemented,
)
from pyspecde.hardware_model.spectrum_interface import SpectrumChannelInterface, SpectrumIntLengths
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
)


class SpectrumCard(SpectrumDevice):
    def __init__(self, device_number: int = 0, ip_address: Optional[str] = None):
        """Class for controlling individual Spectrum digitizer cards.

        Args:
            device_number (int): Index of the card to control. If only one card is present, set to 0.
            ip_address (Optional[str]): If connecting to a networked card, provide the IP address here as a string.

        """
        if ip_address is not None:
            self._visa_string = _create_visa_string_from_ip(ip_address, device_number)
        else:
            self._visa_string = f"/dev/spcm{device_number}"
        self._connect(self._visa_string)
        self._trigger_sources: List[TriggerSource] = []
        self._channels = self._init_channels()
        self._enabled_channels: List[int] = [0]
        self._transfer_buffer: Optional[TransferBuffer] = None
        self.apply_channel_enabling()

    def reconnect(self) -> None:
        """Reconnect to the card after disconnect() has been called."""
        self._connect(self._visa_string)

    @property
    def status(self) -> CARD_STATUS_TYPE:
        """Read the current acquisition status of the card.
        Returns:
            Statuses (CARD_STATUS_TYPE): A list of StatusCode Enums describing the current acquisition status of the
            card. See spectrum_api_wrapper/status.py (and the Spectrum documentation) for the list off possible
            acquisition statuses.
        """
        return decode_status(self.read_spectrum_device_register(SPC_M2STATUS))

    def wait_for_acquisition_to_complete(self) -> None:
        """Blocks until the current acquisition has finished, or the timeout is reached.

        In Standard Single mode (SPC_REC_STD_SINGLE), this should be called after start_acquisition(). Ones the call
        to wait_for_acquisition_to_complete() returns, the newly acquired samples are in the on_device buffer and ready
        for transfer to the TransferBuffer using start_transfer().

        In FIFO mode (SPC_REC_FIFO_SINGLE, SPC_REC_FIFO_MULTI), the card will continue to acquire samples until
        stop_acquisition() is called, so wait_for_acquisition_to_complete() should not be used.

        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_WAITREADY)

    def start_transfer(self) -> None:
        """Transfer acquired waveforms from the on-device buffer to the TransferBuffer.

        Requires that a TransferBuffer has been defined (see define_transfer_buffer()).

        In Standard Single mode (SPC_REC_STD_SINGLE), start_transfer() should be called after each acquisition has
        completed.

        In FIFO mode (SPC_REC_FIFO_SINGLE, SPC_REC_FIFO_MULTI), start_transfer() should be called immediately after
        start_acquisition() has been called, so that the waveform data can be continuously streamed into the transfer
        buffer as it is acquired.
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_DATA_STARTDMA)

    def stop_transfer(self) -> None:
        """Stop the transfer of samples from the on-device buffer to the TransferBuffer.

        This method is rarely required, and may invalidate transferred samples.

        In Standard Single mode (SPC_REC_STD_SINGLE), transfer will automatically stop once all acquired samples have
        been transferred, so stop_transfer() should not be used. Instead, call wait_for_transfer_to_complete() after
        start_transfer().

        In FIFO mode (SPC_REC_FIFO_SINGLE, SPC_REC_FIFO_MULTI), samples are transferred continuously during acquisition,
        and transfer will automatically stop when stop_acquisition() is called as there will be no more samples to
        transfer, so so stop_transfer() should not be used.

        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_DATA_STOPDMA)

    def wait_for_transfer_to_complete(self) -> None:
        """Blocks until the currently active transfer of samples from the on-device buffer to the TransferBuffer is
        complete.

        Used in Standard Single mode (SPC_REC_STD_SINGLE) after starting a transfer. Once the method returns, all
        acquired waveforms have been transferred from the on_device buffer to the TransferBuffer and can be read using
        the get_waveforms() method.

        Not required in FIFO mode (SPC_REC_FIFO_SINGLE, SPC_REC_FIFO_MULTI) because samples are continuously streamed
        until stop_acquisition() is called.
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_DATA_WAITDMA)

    @property
    def transfer_buffers(self) -> List[TransferBuffer]:
        """Return the TransferBuffer object containing the latest transferred samples.

        Returns:
            buffer (List[TransferBuffer]): A length-1 list containing the TransferBuffer object. The samples within the
                TransferBuffer can be accessed using its own interface, but the samples are stored as a 1D array, with
                the samples of each channel interleaved. It is more convenient to read waveform data using the
                get_waveforms() method.

        """
        if self._transfer_buffer is not None:
            return [self._transfer_buffer]
        else:
            raise SpectrumNoTransferBufferDefined("Cannot find TransferBuffer.")

    def define_transfer_buffer(self, buffer: Optional[List[CardToPCDataTransferBuffer]] = None) -> None:
        """Create or provide a CardToPCDataTransferBuffer object for receiving acquired samples from the device.

        Args:
            buffer (Optional[List[CardToPCDataTransferBuffer]]): A length-1 list containing a pre-constructed
            CardToPCDataTransferBuffer  The size of the buffer should be chosen according to the current number of
            active channels and the acquisition length.

        If no buffer is provided, one will be created with the correct size and a board_memory_offset_bytes of 0.
        """
        if buffer:
            self._transfer_buffer = buffer[0]
        else:
            self._transfer_buffer = CardToPCDataTransferBuffer(
                self.acquisition_length_samples * len(self.enabled_channels)
            )
        set_transfer_buffer(self._handle, self._transfer_buffer)

    def get_waveforms(self) -> List[ndarray]:
        """Get a list of of the most recently transferred waveforms.

        This method copies and reshapes the samples in the TransferBuffer into a list of 1D NumPy arrays (waveforms) and
        returns the list.

        In Standard Single mode (SPC_REC_STD_SINGLE), get_waveforms() should be called after
        wait_for_transfer_to_complete() has returned.

        In FIFO mode (SPC_REC_FIFO_SINGLE, SPC_REC_FIFO_MULTI), while the card is continuously acquiring samples and
        transferring them to the TransferBuffer, this method should be called in a loop . The method will block until
        each new transfer is received, so the loop will run at the same rate as the acquisition (in SPC_REC_FIFO_MULTI
        mode, for example, this would the rate at which your trigger source was running).

        Returns:
            waveforms (List[ndarray]): A list of 1D NumPy arrays, one for each channel enabled for the acquisition,
                ordered by channel number.

        """
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            self.wait_for_transfer_to_complete()
            num_available_bytes = self.read_spectrum_device_register(SPC_DATA_AVAIL_USER_LEN)
            self.write_to_spectrum_device_register(SPC_DATA_AVAIL_CARD_LEN, num_available_bytes)
        waveforms_in_columns = copy(self.transfer_buffers[0].data_buffer).reshape(
            (self.acquisition_length_samples, len(self.enabled_channels))
        )
        return [waveform for waveform in waveforms_in_columns.T]

    def disconnect(self) -> None:
        """Terminate the connection to the hardware device."""
        if self.connected:
            destroy_handle(self._handle)
            self._connected = False

    @property
    def connected(self) -> bool:
        """Returns True if a hardware device is currently connected, False if not."""
        return self._connected

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SpectrumCard):
            return self._handle == other._handle
        else:
            raise NotImplementedError()

    @property
    def channels(self) -> List[SpectrumChannelInterface]:
        """A list of channels belonging to the digitizer card.

        Properties of the individual channels (e.g. vertical range) can be set by calling their methods directly.

        """
        return self._channels

    @property
    def enabled_channels(self) -> List[int]:
        """The indices of the currently enabled channels (a list of integers)."""
        return self._enabled_channels

    def set_enabled_channels(self, channels_nums: List[int]) -> None:
        """Change which channels are enabled.

        Args:
            channels_nums (List[int]): The integer channel numbers to enable.
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
            sources (List[TriggerSource]): A list of TriggerSources.
        """
        or_of_sources = self.read_spectrum_device_register(SPC_TRIG_ORMASK)
        self._trigger_sources = decode_trigger_sources(or_of_sources)
        return self._trigger_sources

    def set_trigger_sources(self, sources: List[TriggerSource]) -> None:
        """Change the enabled trigger sources.

        Args:
            sources (List[TriggerSources]): The TriggerSources to enable.
        """
        self._trigger_sources = sources
        or_of_sources = reduce(or_, [s.value for s in sources])
        self.write_to_spectrum_device_register(SPC_TRIG_ORMASK, or_of_sources)
        self.write_to_spectrum_device_register(SPC_TRIG_ANDMASK, 0)

    @property
    def external_trigger_mode(self) -> ExternalTriggerMode:
        """The currently enabled external trigger mode. An external trigger source must be enabled."""
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
        """Change the currently enabled trigger mode. An external trigger source must be enabled."""
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
    def external_trigger_level_mv(self) -> int:
        """The signal level (mV) needed to trigger an acquisition using an external trigger source. An external
        trigger source must be enabled."""
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot get external trigger level.")
        else:
            first_trig_source = self._active_external_triggers[0]
            try:
                return self.read_spectrum_device_register(EXTERNAL_TRIGGER_LEVEL_COMMANDS[first_trig_source.value])
            except KeyError:
                raise SpectrumTriggerOperationNotImplemented(f"Cannot get trigger level of {first_trig_source.name}.")

    def set_external_trigger_level_mv(self, level: int) -> None:
        """Change the signal level (mV) needed to trigger an acquisition using an external trigger source. An external
        trigger source must be enabled."""
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot set external trigger level.")
        else:
            for trigger_source in self._active_external_triggers:
                try:
                    self.write_to_spectrum_device_register(EXTERNAL_TRIGGER_LEVEL_COMMANDS[trigger_source.value], level)
                except KeyError:
                    raise SpectrumTriggerOperationNotImplemented(f"Cannot set trigger level of {trigger_source.name}.")

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

    def _init_channels(self) -> List[SpectrumChannelInterface]:
        num_modules = self.read_spectrum_device_register(SPC_MIINST_MODULES)
        num_channels_per_module = self.read_spectrum_device_register(SPC_MIINST_CHPERMODULE)
        total_channels = num_modules * num_channels_per_module
        return [SpectrumChannel(n, self) for n in range(total_channels)]

    @property
    def acquisition_length_samples(self) -> int:
        """The current recording length (per channel) in samples."""
        return self.read_spectrum_device_register(SPC_MEMSIZE)

    def set_acquisition_length_samples(self, length_in_samples: int) -> None:
        """Change the recording length (per channel). In FIFO mode, it will be quantised to nearest 8 samples."""
        length_in_samples = self._coerce_to_nearest_8_samples_if_fifo(length_in_samples)
        self.write_to_spectrum_device_register(SPC_SEGMENTSIZE, length_in_samples)
        self.write_to_spectrum_device_register(SPC_MEMSIZE, length_in_samples)

    @property
    def post_trigger_length_samples(self) -> int:
        """The number of samples of the recording that will contain data received after the trigger event."""
        return self.read_spectrum_device_register(SPC_POSTTRIGGER)

    def set_post_trigger_length_samples(self, length_in_samples: int) -> None:
        """Change the number of samples of the recording that will contain data received after the trigger event.
        In FIFO mode, this will be quantised to nearest 8 samples with a maximum value 8 samples less than the acquisition
        length."""
        length_in_samples = self._coerce_to_nearest_8_samples_if_fifo(length_in_samples)
        if (self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI) or (
            self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_SINGLE
        ):
            if (self.acquisition_length_samples - length_in_samples) < 8:
                print(
                    "FIFO mode: coercing post trigger length to maximum allowed value (8 samples less than "
                    "the acquisition length)."
                )
                length_in_samples = self.acquisition_length_samples - 8
        self.write_to_spectrum_device_register(SPC_POSTTRIGGER, length_in_samples)

    def _coerce_to_nearest_8_samples_if_fifo(self, value: int) -> int:
        if (self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI) or (
            self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_SINGLE
        ):
            if value != mod(value, 8):
                print("FIFO mode: coercing length to nearest 8 samples")
                value = int(value - mod(value, 8))
        return value

    @property
    def acquisition_mode(self) -> AcquisitionMode:
        """The currently enabled card mode."""
        return AcquisitionMode(self.read_spectrum_device_register(SPC_CARDMODE))

    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        """Change the currently enabled card mode. See AcquisitionMode and the Spectrum documentation
        for the available modes."""
        self.write_to_spectrum_device_register(SPC_CARDMODE, mode.value)

    @property
    def timeout_ms(self) -> int:
        """The time for which the card will wait for a trigger to tbe received after an acquisition has started
        before returning an error."""
        return self.read_spectrum_device_register(SPC_TIMEOUT)

    def set_timeout_ms(self, timeout_in_ms: int) -> None:
        """Change the time for which the card will wait for a trigger to tbe received after an acquisition has started
        before returning an error."""
        self.write_to_spectrum_device_register(SPC_TIMEOUT, timeout_in_ms)

    @property
    def clock_mode(self) -> ClockMode:
        """The currently enabled clock mode."""
        return ClockMode(self.read_spectrum_device_register(SPC_CLOCKMODE))

    def set_clock_mode(self, mode: ClockMode) -> None:
        """Change the clock mode. See ClockMode and the Spectrum documentation for available modes."""
        self.write_to_spectrum_device_register(SPC_CLOCKMODE, mode.value)

    @property
    def available_io_modes(self) -> AvailableIOModes:
        """For each multipurpose IO line on the card, read the available modes. See IOLineMode and the Spectrum
        Documentation for all possible available modes and their meanings."""
        return AvailableIOModes(
            X0=decode_available_io_modes(self.read_spectrum_device_register(SPCM_X0_AVAILMODES)),
            X1=decode_available_io_modes(self.read_spectrum_device_register(SPCM_X1_AVAILMODES)),
            X2=decode_available_io_modes(self.read_spectrum_device_register(SPCM_X2_AVAILMODES)),
            X3=decode_available_io_modes(self.read_spectrum_device_register(SPCM_X3_AVAILMODES)),
        )

    @property
    def feature_list(self) -> Tuple[List[CardFeature], List[AdvancedCardFeature]]:
        """Get a list of the features of the card. See CardFeature, AdvancedCardFeature and the Spectrum
        documentation for more information."""
        normal_features = decode_card_features(self.read_spectrum_device_register(SPC_PCIFEATURES))
        advanced_features = decode_advanced_card_features(self.read_spectrum_device_register(SPC_PCIEXTFEATURES))
        return normal_features, advanced_features

    @property
    def sample_rate_hz(self) -> int:
        """The rate at which samples will be acquired during an acquisition, in Hz."""
        return self.read_spectrum_device_register(SPC_SAMPLERATE, SpectrumIntLengths.SIXTY_FOUR)

    def set_sample_rate_hz(self, rate: int) -> None:
        """Change the rate at which samples will be acquired during an acquisition, in Hz."""
        self.write_to_spectrum_device_register(SPC_SAMPLERATE, rate, SpectrumIntLengths.SIXTY_FOUR)

    def __str__(self) -> str:
        return f"Card {self._visa_string}"


def _create_visa_string_from_ip(ip_address: str, instrument_number: int) -> str:
    return f"TCPIP[0]::{ip_address}::inst{instrument_number}::INSTR"
