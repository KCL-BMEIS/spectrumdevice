from functools import reduce
from operator import or_
from typing import List, Optional

from pyspecde.sdk_translation_layer import (
    DEVICE_HANDLE_TYPE,
    TriggerSource,
    TransferBuffer,
    set_transfer_buffer,
    destroy_handle,
    ExternalTriggerMode,
    EXTERNAL_TRIGGER_MODE_COMMANDS,
    EXTERNAL_TRIGGER_LEVEL_COMMANDS,
    AcquisitionMode,
    ClockMode,
    spectrum_handle_factory,
)
from pyspecde.hardware_model.spectrum_channel import spectrum_channel_factory
from pyspecde.hardware_model.spectrum_device import SpectrumDevice
from pyspecde.spectrum_exceptions import (
    SpectrumNoTransferBufferDefined,
    SpectrumIOError,
    SpectrumExternalTriggerNotEnabled,
    SpectrumTriggerOperationNotImplemented,
)
from pyspecde.hardware_model.spectrum_interface import SpectrumChannelInterface, SpectrumIntLengths
from third_party.specde.py_header.regs import (
    SPC_M2CMD,
    M2CMD_DATA_STARTDMA,
    M2CMD_DATA_STOPDMA,
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
)


class SpectrumCard(SpectrumDevice):
    def __init__(self, handle: DEVICE_HANDLE_TYPE):
        self._handle = handle
        self._trigger_sources: List[TriggerSource] = []
        self._channels = self._init_channels()
        self._transfer_buffer: Optional[TransferBuffer] = None
        self.apply_channel_enabling()

    def start_transfer(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_DATA_STARTDMA)

    def stop_transfer(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_DATA_STOPDMA)

    def wait_for_transfer_to_complete(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_DATA_WAITDMA)

    @property
    def transfer_buffer(self) -> TransferBuffer:
        if self._transfer_buffer is not None:
            return self._transfer_buffer
        else:
            raise SpectrumNoTransferBufferDefined("Cannot find TransferBuffer.")

    def set_transfer_buffer(self, buffer: TransferBuffer) -> None:
        self._transfer_buffer = buffer
        set_transfer_buffer(self.handle, buffer)

    def disconnect(self) -> None:
        destroy_handle(self.handle)

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
        enabled_channel_spectrum_values = [channel.name.value for channel in self.channels if channel.enabled]
        if len(enabled_channel_spectrum_values) > 0:
            bitwise_or_of_enabled_channels = reduce(or_, enabled_channel_spectrum_values)
        else:
            bitwise_or_of_enabled_channels = 0
        self.set_spectrum_api_param(SPC_CHENABLE, bitwise_or_of_enabled_channels)

    def _init_channels(self) -> List[SpectrumChannelInterface]:
        num_modules = self.get_spectrum_api_param(SPC_MIINST_MODULES)
        num_channels_per_module = self.get_spectrum_api_param(SPC_MIINST_CHPERMODULE)
        total_channels = num_modules * num_channels_per_module
        return [spectrum_channel_factory(n, self) for n in range(total_channels)]

    @property
    def acquisition_length_samples(self) -> int:
        return self.get_spectrum_api_param(SPC_MEMSIZE)

    def set_acquisition_length_samples(self, length_in_samples: int) -> None:
        self.set_spectrum_api_param(SPC_MEMSIZE, length_in_samples)

    @property
    def post_trigger_length_samples(self) -> int:
        return self.get_spectrum_api_param(SPC_POSTTRIGGER)

    def set_post_trigger_length_samples(self, length_in_samples: int) -> None:
        self.set_spectrum_api_param(SPC_POSTTRIGGER, length_in_samples)

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
    def sample_rate_hz(self) -> int:
        return self.get_spectrum_api_param(SPC_SAMPLERATE, SpectrumIntLengths.SIXTY_FOUR)

    def set_sample_rate_hz(self, rate: int) -> None:
        self.set_spectrum_api_param(SPC_SAMPLERATE, rate, SpectrumIntLengths.SIXTY_FOUR)


def spectrum_card_factory(visa_string: str) -> SpectrumCard:
    return SpectrumCard(spectrum_handle_factory(visa_string))
