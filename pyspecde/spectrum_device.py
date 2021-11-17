from abc import ABC
from functools import reduce
from operator import or_
from typing import List, Optional

from pyspecde.spectrum_exceptions import (
    SpectrumIOError,
    SpectrumExternalTriggerNotEnabled,
    SpectrumNoTransferBufferDefined,
    SpectrumTriggerOperationNotImplemented,
)
from third_party.specde.py_header.regs import (
    SPC_MIINST_MODULES,
    SPC_MIINST_CHPERMODULE,
    SPC_CHENABLE,
    SPC_MEMSIZE,
    SPC_POSTTRIGGER,
    SPC_CARDMODE,
    SPC_TIMEOUT,
    SPC_TRIG_ORMASK,
    SPC_TRIG_ANDMASK,
    SPC_CLOCKMODE,
    SPC_SAMPLERATE,
    M2CMD_CARD_START,
    SPC_M2CMD,
    M2CMD_DATA_STARTDMA,
    M2CMD_CARD_ENABLETRIGGER,
    M2CMD_CARD_STOP,
    M2CMD_CARD_DISABLETRIGGER,
    M2CMD_DATA_STOPDMA,
)

from pyspecde.spectrum_interface import (
    SpectrumInterface,
    SpectrumChannelInterface,
    SpectrumIntLengths,
)
from pyspecde.sdk_translation_layer import (
    DEVICE_HANDLE_TYPE,
    TransferBuffer,
    AcquisitionMode,
    TriggerSource,
    ExternalTriggerMode,
    EXTERNAL_TRIGGER_MODE_COMMANDS,
    EXTERNAL_TRIGGER_LEVEL_COMMANDS,
    ClockMode,
    VERTICAL_RANGE_COMMANDS,
    VERTICAL_OFFSET_COMMANDS,
    SpectrumChannelName,
    spectrum_handle_factory,
    destroy_handle,
    get_spectrum_i32_api_param,
    get_spectrum_i64_api_param,
    set_spectrum_i32_api_param,
    set_spectrum_i64_api_param,
    set_transfer_buffer,
)


def create_visa_string_from_ip(ip_address: str, instrument_number: int) -> str:
    return f"TCPIP::{ip_address}::inst{instrument_number}::INSTR"


class SpectrumChannel(SpectrumChannelInterface):
    def __init__(self, name: SpectrumChannelName, parent_device: SpectrumInterface):
        self._name: SpectrumChannelName = name
        self._parent_device = parent_device
        self._enabled = True

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SpectrumChannel):
            return (self.name == other.name) and (self._parent_device == other._parent_device)
        else:
            raise NotImplementedError()

    @property
    def name(self) -> SpectrumChannelName:
        return self._name

    @property
    def _number(self) -> int:
        return int(self.name.name.split("CHANNEL")[-1])

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self._parent_device.apply_channel_enabling()

    @property
    def vertical_range_mv(self) -> int:
        return self._parent_device.get_spectrum_api_param(VERTICAL_RANGE_COMMANDS[self._number])

    def set_vertical_range_mv(self, vertical_range: int) -> None:
        self._parent_device.set_spectrum_api_param(VERTICAL_RANGE_COMMANDS[self._number], vertical_range)

    @property
    def vertical_offset_percent(self) -> int:
        return self._parent_device.get_spectrum_api_param(VERTICAL_OFFSET_COMMANDS[self._number])

    def set_vertical_offset_percent(self, offset: int) -> None:
        self._parent_device.set_spectrum_api_param(VERTICAL_OFFSET_COMMANDS[self._number], offset)


def spectrum_channel_factory(channel_number: int, parent_device: SpectrumInterface) -> SpectrumChannel:
    return SpectrumChannel(SpectrumChannelName[f"CHANNEL{channel_number}"], parent_device)


class SpectrumDevice(SpectrumInterface, ABC):
    def run(self) -> None:
        self.start_dma()
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)

    def stop(self) -> None:
        self.stop_dma()
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_CARD_STOP | M2CMD_CARD_DISABLETRIGGER)

    def set_spectrum_api_param(
        self,
        spectrum_command: int,
        value: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> None:
        if length == SpectrumIntLengths.THIRTY_TWO:
            set_spectrum_i32_api_param(self.handle, spectrum_command, value)
        elif length == SpectrumIntLengths.SIXTY_FOUR:
            set_spectrum_i64_api_param(self.handle, spectrum_command, value)
        else:
            raise ValueError("Spectrum integer length not recognised.")

    def get_spectrum_api_param(
        self,
        spectrum_command: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> int:
        if length == SpectrumIntLengths.THIRTY_TWO:
            return get_spectrum_i32_api_param(self.handle, spectrum_command)
        elif length == SpectrumIntLengths.SIXTY_FOUR:
            return get_spectrum_i64_api_param(self.handle, spectrum_command)
        else:
            raise ValueError("Spectrum integer length not recognised.")


class SpectrumCard(SpectrumDevice):
    def __init__(self, handle: DEVICE_HANDLE_TYPE):
        self._handle = handle
        self._trigger_sources: List[TriggerSource] = []
        self._channels = self._init_channels()
        self._transfer_buffer: Optional[TransferBuffer] = None
        self.apply_channel_enabling()

    def start_dma(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_DATA_STARTDMA)

    def stop_dma(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_DATA_STOPDMA)

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
            TriggerSource(val) for val in list(set(EXTERNAL_TRIGGER_MODE_COMMANDS.keys()) & set(self._trigger_sources))
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
        bitwise_or_of_enabled_channels = reduce(or_, enabled_channel_spectrum_values)
        self.set_spectrum_api_param(SPC_CHENABLE, bitwise_or_of_enabled_channels)

    def _init_channels(self) -> List[SpectrumChannelInterface]:
        num_modules = self.get_spectrum_api_param(SPC_MIINST_MODULES)
        num_channels_per_module = self.get_spectrum_api_param(SPC_MIINST_CHPERMODULE)
        total_channels = num_modules * num_channels_per_module
        return [spectrum_channel_factory(n, self) for n in range(total_channels)]

    @property
    def acquisition_length_bytes(self) -> int:
        return self.get_spectrum_api_param(SPC_MEMSIZE)

    def set_acquisition_length_bytes(self, length_in_bytes: int) -> None:
        self.set_spectrum_api_param(SPC_MEMSIZE, length_in_bytes)

    @property
    def post_trigger_length_bytes(self) -> int:
        return self.get_spectrum_api_param(SPC_POSTTRIGGER)

    def set_post_trigger_length_bytes(self, length_in_bytes: int) -> None:
        self.set_spectrum_api_param(SPC_POSTTRIGGER, length_in_bytes)

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
