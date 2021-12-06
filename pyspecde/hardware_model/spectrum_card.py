from copy import copy
from functools import reduce
from operator import or_
from typing import List, Optional, Tuple

from numpy import ndarray, mod

from pyspecde.sdk_translation_layer import (
    CARD_STATUS_TYPE,
    DEVICE_HANDLE_TYPE,
    TriggerSource,
    TransferBuffer,
    decode_status,
    set_transfer_buffer,
    destroy_handle,
    ExternalTriggerMode,
    EXTERNAL_TRIGGER_MODE_COMMANDS,
    EXTERNAL_TRIGGER_LEVEL_COMMANDS,
    AcquisitionMode,
    ClockMode,
    spectrum_handle_factory,
    transfer_buffer_factory,
    decode_available_io_modes,
    CardFeature,
    decode_card_features,
    decode_advanced_card_features,
    AdvancedCardFeature,
    AvailableIOModes,
)
from pyspecde.hardware_model.spectrum_channel import spectrum_channel_factory
from pyspecde.hardware_model.spectrum_device import SpectrumDevice
from pyspecde.spectrum_exceptions import (
    SpectrumInvalidNumberOfEnabledChannels,
    SpectrumNoTransferBufferDefined,
    SpectrumIOError,
    SpectrumExternalTriggerNotEnabled,
    SpectrumTriggerOperationNotImplemented,
)
from pyspecde.hardware_model.spectrum_interface import SpectrumChannelInterface, SpectrumIntLengths
from third_party.specde.py_header.regs import (
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
    def __init__(self, handle: DEVICE_HANDLE_TYPE):
        self._handle = handle
        self._connected = True
        self._trigger_sources: List[TriggerSource] = []
        self._channels = self._init_channels()
        self._enabled_channels: List[int] = [0]
        self._transfer_buffer: Optional[TransferBuffer] = None
        self.apply_channel_enabling()

    @property
    def status(self) -> CARD_STATUS_TYPE:
        return decode_status(self.get_spectrum_api_param(SPC_M2STATUS))

    def start_transfer(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_DATA_STARTDMA)

    def stop_transfer(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_DATA_STOPDMA)

    def wait_for_transfer_to_complete(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_DATA_WAITDMA)

    @property
    def transfer_buffers(self) -> List[TransferBuffer]:
        if self._transfer_buffer is not None:
            return [self._transfer_buffer]
        else:
            raise SpectrumNoTransferBufferDefined("Cannot find TransferBuffer.")

    def define_transfer_buffer(self, buffer: Optional[TransferBuffer] = None) -> None:
        if buffer:
            self._transfer_buffer = buffer
        else:
            self._transfer_buffer = transfer_buffer_factory(
                self.acquisition_length_samples * len(self.enabled_channels)
            )
        set_transfer_buffer(self.handle, self._transfer_buffer)

    def get_waveforms(self) -> List[ndarray]:
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            self.wait_for_transfer_to_complete()
            num_available_bytes = self.get_spectrum_api_param(SPC_DATA_AVAIL_USER_LEN)
            self.set_spectrum_api_param(SPC_DATA_AVAIL_CARD_LEN, num_available_bytes)
        waveforms_in_columns = copy(self.transfer_buffers[0].data_buffer).reshape(
            (self.acquisition_length_samples, len(self.enabled_channels))
        )
        return [waveform for waveform in waveforms_in_columns.T]

    def wait_for_acquisition_to_complete(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_CARD_WAITREADY)

    def disconnect(self) -> None:
        if self.connected:
            destroy_handle(self.handle)
            self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def handle(self) -> DEVICE_HANDLE_TYPE:
        return self._handle

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SpectrumCard):
            return self._handle == other._handle
        else:
            raise NotImplementedError()

    @property
    def channels(self) -> List[SpectrumChannelInterface]:
        return self._channels

    @property
    def enabled_channels(self) -> List[int]:
        return self._enabled_channels

    def set_enabled_channels(self, channels_nums: List[int]) -> None:
        if len(channels_nums) in [1, 2, 4, 8]:
            self._enabled_channels = channels_nums
            self.apply_channel_enabling()
        else:
            raise SpectrumInvalidNumberOfEnabledChannels(f"{len(channels_nums)} cannot be enabled at once.")

    @property
    def trigger_sources(self) -> List[TriggerSource]:
        or_of_sources = self.get_spectrum_api_param(SPC_TRIG_ORMASK)
        if or_of_sources != reduce(or_, [s.value for s in self._trigger_sources]):
            raise SpectrumIOError("Trigger sources configured on device do not match those previously set.")
        else:
            return self._trigger_sources

    def set_trigger_sources(self, sources: List[TriggerSource]) -> None:
        self._trigger_sources = sources
        or_of_sources = reduce(or_, [s.value for s in sources])
        self.set_spectrum_api_param(SPC_TRIG_ORMASK, or_of_sources)
        self.set_spectrum_api_param(SPC_TRIG_ANDMASK, 0)

    @property
    def external_trigger_mode(self) -> ExternalTriggerMode:
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot get external trigger mode.")
        else:
            first_trig_source = self._active_external_triggers[0]
            try:
                return ExternalTriggerMode(
                    self.get_spectrum_api_param(EXTERNAL_TRIGGER_MODE_COMMANDS[first_trig_source.value])
                )
            except KeyError:
                raise SpectrumTriggerOperationNotImplemented(f"Cannot get trigger mode of {first_trig_source.name}.")

    def set_external_trigger_mode(self, mode: ExternalTriggerMode) -> None:
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot set external trigger mode.")
        else:
            for trigger_source in self._active_external_triggers:
                try:
                    self.set_spectrum_api_param(EXTERNAL_TRIGGER_MODE_COMMANDS[trigger_source.value], mode.value)
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
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot get external trigger level.")
        else:
            first_trig_source = self._active_external_triggers[0]
            try:
                return self.get_spectrum_api_param(EXTERNAL_TRIGGER_LEVEL_COMMANDS[first_trig_source.value])
            except KeyError:
                raise SpectrumTriggerOperationNotImplemented(f"Cannot get trigger level of {first_trig_source.name}.")

    def set_external_trigger_level_mv(self, level: int) -> None:
        if len(self._active_external_triggers) == 0:
            raise SpectrumExternalTriggerNotEnabled("Cannot set external trigger level.")
        else:
            for trigger_source in self._active_external_triggers:
                try:
                    self.set_spectrum_api_param(EXTERNAL_TRIGGER_LEVEL_COMMANDS[trigger_source.value], level)
                except KeyError:
                    raise SpectrumTriggerOperationNotImplemented(f"Cannot set trigger level of {trigger_source.name}.")

    def apply_channel_enabling(self) -> None:
        enabled_channel_spectrum_values = [self.channels[i].name.value for i in self._enabled_channels]
        if len(enabled_channel_spectrum_values) in [1, 2, 4, 8]:
            bitwise_or_of_enabled_channels = reduce(or_, enabled_channel_spectrum_values)
            self.set_spectrum_api_param(SPC_CHENABLE, bitwise_or_of_enabled_channels)
        else:
            raise SpectrumInvalidNumberOfEnabledChannels(
                f"Cannot enable {len(enabled_channel_spectrum_values)} " f"channels on one card."
            )

    def _init_channels(self) -> List[SpectrumChannelInterface]:
        num_modules = self.get_spectrum_api_param(SPC_MIINST_MODULES)
        num_channels_per_module = self.get_spectrum_api_param(SPC_MIINST_CHPERMODULE)
        total_channels = num_modules * num_channels_per_module
        return [spectrum_channel_factory(n, self) for n in range(total_channels)]

    @property
    def acquisition_length_samples(self) -> int:
        return self.get_spectrum_api_param(SPC_MEMSIZE)

    def set_acquisition_length_samples(self, length_in_samples: int) -> None:
        """In FIFO mode, this is quantised to nearest 8 samples."""
        length_in_samples = self._coerce_to_nearest_8_samples_if_fifo(length_in_samples)
        self.set_spectrum_api_param(SPC_SEGMENTSIZE, length_in_samples)
        self.set_spectrum_api_param(SPC_MEMSIZE, length_in_samples)

    @property
    def post_trigger_length_samples(self) -> int:
        return self.get_spectrum_api_param(SPC_POSTTRIGGER)

    def set_post_trigger_length_samples(self, length_in_samples: int) -> None:
        """In FIFO mode, this is quantised to nearest 8 samples with a maximum value 8 samples less than the
        acquisition length."""
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
        self.set_spectrum_api_param(SPC_POSTTRIGGER, length_in_samples)

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
        return AcquisitionMode(self.get_spectrum_api_param(SPC_CARDMODE))

    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        self.set_spectrum_api_param(SPC_CARDMODE, mode.value)

    @property
    def timeout_ms(self) -> int:
        return self.get_spectrum_api_param(SPC_TIMEOUT)

    def set_timeout_ms(self, timeout_in_ms: int) -> None:
        self.set_spectrum_api_param(SPC_TIMEOUT, timeout_in_ms)

    @property
    def clock_mode(self) -> ClockMode:
        return ClockMode(self.get_spectrum_api_param(SPC_CLOCKMODE))

    def set_clock_mode(self, mode: ClockMode) -> None:
        self.set_spectrum_api_param(SPC_CLOCKMODE, mode.value)

    @property
    def available_io_modes(self) -> AvailableIOModes:

        return AvailableIOModes(
            X0=decode_available_io_modes(self.get_spectrum_api_param(SPCM_X0_AVAILMODES)),
            X1=decode_available_io_modes(self.get_spectrum_api_param(SPCM_X1_AVAILMODES)),
            X2=decode_available_io_modes(self.get_spectrum_api_param(SPCM_X2_AVAILMODES)),
            X3=decode_available_io_modes(self.get_spectrum_api_param(SPCM_X3_AVAILMODES)),
        )

    @property
    def feature_list(self) -> Tuple[List[CardFeature], List[AdvancedCardFeature]]:
        normal_features = decode_card_features(self.get_spectrum_api_param(SPC_PCIFEATURES))
        advanced_features = decode_advanced_card_features(self.get_spectrum_api_param(SPC_PCIEXTFEATURES))
        return normal_features, advanced_features

    @property
    def sample_rate_hz(self) -> int:
        return self.get_spectrum_api_param(SPC_SAMPLERATE, SpectrumIntLengths.SIXTY_FOUR)

    def set_sample_rate_hz(self, rate: int) -> None:
        self.set_spectrum_api_param(SPC_SAMPLERATE, rate, SpectrumIntLengths.SIXTY_FOUR)


def spectrum_card_factory(visa_string: str) -> SpectrumCard:
    return SpectrumCard(spectrum_handle_factory(visa_string))
