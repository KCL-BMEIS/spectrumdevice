from ctypes import byref, create_string_buffer, c_void_p
from functools import reduce
from operator import or_
from typing import List, NewType

from pyspecde.spectrum_exceptions import SpectrumIOError
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
)

try:
    from third_party.specde.pyspcm import (
        int32,
        spcm_dwGetParam_i32,
        spcm_dwSetParam_i32,
        spcm_hOpen,
        spcm_vClose,
        spcm_dwSetParam_i64,
        int64,
        spcm_dwGetParam_i64,
    )
except OSError:
    from tests.mock_pyspcm import (
        int32,
        spcm_dwGetParam_i32,
        spcm_dwSetParam_i32,
        spcm_hOpen,
        spcm_vClose,
        spcm_dwSetParam_i64,
        int64,
        spcm_dwGetParam_i64,
    )
from pyspecde.spectrum_interface import (
    SpectrumInterface,
    AcquisitionMode,
    TriggerSource,
    ClockMode,
    SpectrumChannelName,
    SpectrumChannelInterface,
    SpectrumIntLengths,
    VERTICAL_RANGE_COMMANDS,
    VERTICAL_OFFSET_COMMANDS,
)

DEVICE_HANDLE_TYPE = NewType("DEVICE_HANDLE_TYPE", c_void_p)


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


class SpectrumDevice(SpectrumInterface):
    def __init__(self, handle: DEVICE_HANDLE_TYPE):
        self._handle = handle
        self._trigger_sources: List[TriggerSource] = []
        self._channels = self._init_channels()
        self.apply_channel_enabling()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SpectrumDevice):
            return self._handle == other._handle
        else:
            raise NotImplementedError()

    def disconnect(self) -> None:
        spcm_vClose(self._handle)

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
    def channels(self) -> List[SpectrumChannelInterface]:
        return self._channels

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
    def clock_mode(self) -> ClockMode:
        return ClockMode(self.get_spectrum_api_param(SPC_CLOCKMODE))

    def set_clock_mode(self, mode: ClockMode) -> None:
        self.set_spectrum_api_param(SPC_CLOCKMODE, mode.value)

    @property
    def sample_rate_hz(self) -> int:
        return self.get_spectrum_api_param(SPC_SAMPLERATE, SpectrumIntLengths.SIXTY_FOUR)

    def set_sample_rate_hz(self, rate: int) -> None:
        self.set_spectrum_api_param(SPC_SAMPLERATE, rate, SpectrumIntLengths.SIXTY_FOUR)

    def set_spectrum_api_param(
        self,
        spectrum_command: int,
        value: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> None:
        if length == SpectrumIntLengths.THIRTY_TWO:
            set_param_callable = spcm_dwSetParam_i32
        elif length == SpectrumIntLengths.SIXTY_FOUR:
            set_param_callable = spcm_dwSetParam_i64
        else:
            raise ValueError("Spectrum integer length not recognised.")
        set_param_callable(self._handle, spectrum_command, value)

    def get_spectrum_api_param(
        self,
        spectrum_command: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> int:
        if length == SpectrumIntLengths.THIRTY_TWO:
            param = int32(0)
            get_param_callable = spcm_dwGetParam_i32
        elif length == SpectrumIntLengths.SIXTY_FOUR:
            param = int64(0)  # type: ignore
            get_param_callable = spcm_dwGetParam_i64
        else:
            raise ValueError("Spectrum integer length not recognised.")
        get_param_callable(self._handle, spectrum_command, byref(param))
        return param.value


def spectrum_device_factory(visa_string: str) -> SpectrumDevice:
    return SpectrumDevice(DEVICE_HANDLE_TYPE(spcm_hOpen(create_string_buffer(bytes(visa_string, encoding="utf8")))))


def networked_spectrum_device_factory(ip_address: str, device_number: int) -> SpectrumDevice:
    return spectrum_device_factory(create_visa_string_from_ip(ip_address, device_number))
