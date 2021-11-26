from ctypes import c_void_p, create_string_buffer, byref
from dataclasses import dataclass
from enum import Enum, EnumMeta
from functools import wraps
from typing import Dict, List, NewType, Callable, Any

from numpy import ndarray, zeros, int16

from pyspecde.spectrum_exceptions import SpectrumApiCallFailed, SpectrumIOError
from third_party.specde.py_header.regs import (
    M2STAT_CARD_PRETRIGGER,
    M2STAT_CARD_READY,
    M2STAT_CARD_SEGMENT_PRETRG,
    M2STAT_CARD_TRIGGER,
    M2STAT_DATA_BLOCKREADY,
    M2STAT_DATA_END,
    M2STAT_DATA_ERROR,
    M2STAT_DATA_OVERRUN,
    M2STAT_NONE,
    SPC_REC_STD_SINGLE,
    SPC_REC_FIFO_MULTI,
    SPC_TMASK_SOFTWARE,
    SPC_TMASK_EXT0,
    SPC_TMASK_EXT1,
    SPC_TMASK_EXT2,
    SPC_TMASK_EXT3,
    SPC_TM_NONE,
    SPC_TM_POS,
    SPC_TRIG_EXT0_MODE,
    SPC_TRIG_EXT1_MODE,
    SPC_TRIG_EXT2_MODE,
    SPC_TRIG_EXT3_MODE,
    SPC_TRIG_EXT0_LEVEL0,
    SPC_TRIG_EXT1_LEVEL0,
    SPC_TRIG_EXT2_LEVEL0,
    SPC_CM_INTPLL,
    SPC_AMP0,
    SPC_AMP1,
    SPC_AMP2,
    SPC_AMP3,
    SPC_AMP4,
    SPC_AMP5,
    SPC_AMP6,
    SPC_AMP7,
    SPC_AMP8,
    SPC_AMP9,
    SPC_AMP10,
    SPC_AMP11,
    SPC_AMP12,
    SPC_AMP13,
    SPC_AMP14,
    SPC_AMP15,
    SPC_OFFS0,
    SPC_OFFS1,
    SPC_OFFS2,
    SPC_OFFS3,
    SPC_OFFS4,
    SPC_OFFS5,
    SPC_OFFS6,
    SPC_OFFS7,
    SPC_OFFS8,
    SPC_OFFS9,
    SPC_OFFS10,
    SPC_OFFS11,
    SPC_OFFS12,
    SPC_OFFS13,
    SPC_OFFS14,
    SPC_OFFS15,
    CHANNEL0,
    CHANNEL1,
    CHANNEL2,
    CHANNEL3,
    CHANNEL4,
    CHANNEL5,
    CHANNEL6,
    CHANNEL7,
    CHANNEL8,
    CHANNEL9,
    CHANNEL10,
    CHANNEL11,
    CHANNEL12,
    CHANNEL13,
    CHANNEL14,
    CHANNEL15,
    SPC_REC_FIFO_SINGLE,
    SPCM_XMODE_DISABLE,
    SPCM_XMODE_ASYNCIN,
    SPCM_XMODE_ASYNCOUT,
    SPCM_XMODE_DIGIN,
    SPCM_XMODE_TRIGIN,
    SPCM_XMODE_DIGOUT,
    SPCM_XMODE_TRIGOUT,
    SPCM_XMODE_RUNSTATE,
    SPCM_XMODE_ARMSTATE,
    SPCM_XMODE_CONTOUTMARK,
    SPCM_FEAT_MULTI,
    SPCM_FEAT_GATE,
    SPCM_FEAT_STARHUB6_EXTM,
    SPCM_FEAT_TIMESTAMP,
    SPCM_FEAT_DIGITAL,
    SPCM_FEAT_STARHUB8_EXTM,
    SPCM_FEAT_STARHUB4,
    SPCM_FEAT_STARHUB5,
    SPCM_FEAT_STARHUB16_EXTM,
    SPCM_FEAT_STARHUB8,
    SPCM_FEAT_STARHUB16,
    SPCM_FEAT_ABA,
    SPCM_FEAT_BASEXIO,
    SPCM_FEAT_AMPLIFIER_10V,
    SPCM_FEAT_STARHUBSYSMASTER,
    SPCM_FEAT_DIFFMODE,
    SPCM_FEAT_SEQUENCE,
    SPCM_FEAT_AMPMODULE_10V,
    SPCM_FEAT_STARHUBSYSSLAVE,
    SPCM_FEAT_NETBOX,
    SPCM_FEAT_REMOTESERVER,
    SPCM_FEAT_SCAPP,
    SPCM_FEAT_CUSTOMMOD_MASK,
    SPCM_FEAT_EXTFW_SEGSTAT,
    SPCM_FEAT_EXTFW_SEGAVERAGE,
    SPCM_FEAT_EXTFW_BOXCAR,
)
from third_party.specde.py_header.spcerr import (
    ERR_INVALIDHANDLE,
    ERR_OK,
    ERR_LASTERR,
    ERR_RUNNING,
    ERR_SETUP,
    ERR_TIMEOUT,
    ERR_ABORT,
    ERR_VALUE,
)

try:
    from third_party.specde.pyspcm import (
        SPCM_BUF_DATA,
        SPCM_BUF_ABA,
        SPCM_BUF_TIMESTAMP,
        SPCM_DIR_PCTOCARD,
        SPCM_DIR_CARDTOPC,
        spcm_dwSetParam_i32,
        spcm_dwSetParam_i64,
        spcm_hOpen,
        spcm_vClose,
        int32,
        spcm_dwGetParam_i32,
        spcm_dwGetParam_i64,
        int64,
        spcm_dwDefTransfer_i64,
    )

    SPECTRUM_DRIVERS_FOUND = True
except OSError:
    from tests.mock_pyspcm import (
        SPCM_BUF_DATA,
        SPCM_BUF_ABA,
        SPCM_BUF_TIMESTAMP,
        SPCM_DIR_PCTOCARD,
        SPCM_DIR_CARDTOPC,
        spcm_dwSetParam_i32,
        spcm_dwSetParam_i64,
        spcm_hOpen,
        spcm_vClose,
        int32,
        spcm_dwGetParam_i32,
        spcm_dwGetParam_i64,
        int64,
        spcm_dwDefTransfer_i64,
    )

    print("Spectrum drivers not found. Hardware cannot be communicated with. Tests can be run in MOCK_HARDWARE mode.")
    SPECTRUM_DRIVERS_FOUND = False

DEVICE_HANDLE_TYPE = NewType("DEVICE_HANDLE_TYPE", c_void_p)


class BufferType(Enum):
    SPCM_BUF_DATA = SPCM_BUF_DATA
    SPCM_BUF_ABA = SPCM_BUF_ABA
    SPCM_BUF_TIMESTAMP = SPCM_BUF_TIMESTAMP


class BufferDirection(Enum):
    SPCM_DIR_PCTOCARD = SPCM_DIR_PCTOCARD
    SPCM_DIR_CARDTOPC = SPCM_DIR_CARDTOPC


@dataclass
class TransferBuffer:
    type: BufferType
    direction: BufferDirection
    board_memory_offset_bytes: int
    data_buffer: ndarray

    @property
    def data_buffer_pointer(self) -> c_void_p:
        return self.data_buffer.ctypes.data_as(c_void_p)

    @property
    def data_buffer_length_bytes(self) -> int:
        return self.data_buffer.size * self.data_buffer.itemsize

    @property
    def notify_size_bytes(self) -> int:
        return self.data_buffer.size * self.data_buffer.itemsize

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TransferBuffer):
            return (
                (self.type == other.type)
                and (self.direction == other.direction)
                and (self.board_memory_offset_bytes == other.board_memory_offset_bytes)
                and (self.data_buffer == other.data_buffer).all()
            )
        else:
            raise NotImplementedError()


def transfer_buffer_factory(
    size_in_samples: int,
    type: BufferType = BufferType.SPCM_BUF_DATA,
    direction: BufferDirection = BufferDirection.SPCM_DIR_CARDTOPC,
) -> TransferBuffer:
    data_buffer = zeros(size_in_samples, int16)
    return TransferBuffer(type=type, direction=direction, board_memory_offset_bytes=0, data_buffer=data_buffer)


class StatusCode(Enum):
    M2STAT_NONE = M2STAT_NONE
    M2STAT_CARD_PRETRIGGER = M2STAT_CARD_PRETRIGGER
    M2STAT_CARD_TRIGGER = M2STAT_CARD_TRIGGER
    M2STAT_CARD_READY = M2STAT_CARD_READY
    M2STAT_CARD_SEGMENT_PRETRG = M2STAT_CARD_SEGMENT_PRETRG
    M2STAT_DATA_BLOCKREADY = M2STAT_DATA_BLOCKREADY
    M2STAT_DATA_END = M2STAT_DATA_END
    M2STAT_DATA_OVERRUN = M2STAT_DATA_OVERRUN
    M2STAT_DATA_ERROR = M2STAT_DATA_ERROR
    M2STAT_EXTRA_BLOCKREADY = M2STAT_DATA_BLOCKREADY
    M2STAT_EXTRA_END = M2STAT_DATA_END
    M2STAT_EXTRA_OVERRUN = M2STAT_DATA_OVERRUN
    M2STAT_EXTRA_ERROR = M2STAT_DATA_ERROR


CARD_STATUS_TYPE = NewType("CARD_STATUS_TYPE", List[StatusCode])
STAR_HUB_STATUS_TYPE = NewType("STAR_HUB_STATUS_TYPE", List[CARD_STATUS_TYPE])


def decode_status(code: int) -> CARD_STATUS_TYPE:
    possible_codes = [code.value for code in StatusCode]
    return CARD_STATUS_TYPE([StatusCode(found_code) for found_code in _decode_bitmap_using_enum(code, possible_codes)])


class AcquisitionMode(Enum):
    SPC_REC_STD_SINGLE = SPC_REC_STD_SINGLE
    SPC_REC_FIFO_SINGLE = SPC_REC_FIFO_SINGLE
    SPC_REC_FIFO_MULTI = SPC_REC_FIFO_MULTI


class TriggerSource(Enum):
    SPC_TMASK_SOFTWARE = SPC_TMASK_SOFTWARE
    SPC_TMASK_EXT0 = SPC_TMASK_EXT0
    SPC_TMASK_EXT1 = SPC_TMASK_EXT1
    SPC_TMASK_EXT2 = SPC_TMASK_EXT2
    SPC_TMASK_EXT3 = SPC_TMASK_EXT3
    SPC_TM_NONE = SPC_TM_NONE


class ExternalTriggerMode(Enum):
    SPC_TM_POS = SPC_TM_POS


EXTERNAL_TRIGGER_MODE_COMMANDS = {
    SPC_TMASK_EXT0: SPC_TRIG_EXT0_MODE,
    SPC_TMASK_EXT1: SPC_TRIG_EXT1_MODE,
    SPC_TMASK_EXT2: SPC_TRIG_EXT2_MODE,
    SPC_TMASK_EXT3: SPC_TRIG_EXT3_MODE,
}
EXTERNAL_TRIGGER_LEVEL_COMMANDS = {
    SPC_TMASK_EXT0: SPC_TRIG_EXT0_LEVEL0,
    SPC_TMASK_EXT1: SPC_TRIG_EXT1_LEVEL0,
    SPC_TMASK_EXT2: SPC_TRIG_EXT2_LEVEL0,
}


class ClockMode(Enum):
    SPC_CM_INTPLL = SPC_CM_INTPLL


VERTICAL_RANGE_COMMANDS = (
    SPC_AMP0,
    SPC_AMP1,
    SPC_AMP2,
    SPC_AMP3,
    SPC_AMP4,
    SPC_AMP5,
    SPC_AMP6,
    SPC_AMP7,
    SPC_AMP8,
    SPC_AMP9,
    SPC_AMP10,
    SPC_AMP11,
    SPC_AMP12,
    SPC_AMP13,
    SPC_AMP14,
    SPC_AMP15,
)
VERTICAL_OFFSET_COMMANDS = (
    SPC_OFFS0,
    SPC_OFFS1,
    SPC_OFFS2,
    SPC_OFFS3,
    SPC_OFFS4,
    SPC_OFFS5,
    SPC_OFFS6,
    SPC_OFFS7,
    SPC_OFFS8,
    SPC_OFFS9,
    SPC_OFFS10,
    SPC_OFFS11,
    SPC_OFFS12,
    SPC_OFFS13,
    SPC_OFFS14,
    SPC_OFFS15,
)


class SpectrumChannelName(Enum):
    CHANNEL0 = CHANNEL0
    CHANNEL1 = CHANNEL1
    CHANNEL2 = CHANNEL2
    CHANNEL3 = CHANNEL3
    CHANNEL4 = CHANNEL4
    CHANNEL5 = CHANNEL5
    CHANNEL6 = CHANNEL6
    CHANNEL7 = CHANNEL7
    CHANNEL8 = CHANNEL8
    CHANNEL9 = CHANNEL9
    CHANNEL10 = CHANNEL10
    CHANNEL11 = CHANNEL11
    CHANNEL12 = CHANNEL12
    CHANNEL13 = CHANNEL13
    CHANNEL14 = CHANNEL14
    CHANNEL15 = CHANNEL15


class IOLineMode(Enum):
    SPCM_XMODE_DISABLE = SPCM_XMODE_DISABLE
    SPCM_XMODE_ASYNCIN = SPCM_XMODE_ASYNCIN
    SPCM_XMODE_ASYNCOUT = SPCM_XMODE_ASYNCOUT
    SPCM_XMODE_DIGIN = SPCM_XMODE_DIGIN
    SPCM_XMODE_TRIGIN = SPCM_XMODE_TRIGIN
    SPCM_XMODE_DIGOUT = SPCM_XMODE_DIGOUT
    SPCM_XMODE_TRIGOUT = SPCM_XMODE_TRIGOUT
    SPCM_XMODE_RUNSTATE = SPCM_XMODE_RUNSTATE
    SPCM_XMODE_ARMSTATE = SPCM_XMODE_ARMSTATE
    SPCM_XMODE_CONTOUTMARK = SPCM_XMODE_CONTOUTMARK


def decode_available_io_modes(value: int) -> List[IOLineMode]:
    possible_values = [mode.value for mode in IOLineMode]
    return [IOLineMode(found_value) for found_value in _decode_bitmap_using_enum(value, possible_values)]


class CardFeature(Enum):
    SPCM_FEAT_MULTI = SPCM_FEAT_MULTI
    SPCM_FEAT_GATE = SPCM_FEAT_GATE
    SPCM_FEAT_DIGITAL = SPCM_FEAT_DIGITAL
    SPCM_FEAT_TIMESTAMP = SPCM_FEAT_TIMESTAMP
    SPCM_FEAT_STARHUB6_EXTM = SPCM_FEAT_STARHUB6_EXTM
    SPCM_FEAT_STARHUB8_EXTM = SPCM_FEAT_STARHUB8_EXTM
    SPCM_FEAT_STARHUB4 = SPCM_FEAT_STARHUB4
    SPCM_FEAT_STARHUB5 = SPCM_FEAT_STARHUB5
    SPCM_FEAT_STARHUB16_EXTM = SPCM_FEAT_STARHUB16_EXTM
    SPCM_FEAT_STARHUB8 = SPCM_FEAT_STARHUB8
    SPCM_FEAT_STARHUB16 = SPCM_FEAT_STARHUB16
    SPCM_FEAT_ABA = SPCM_FEAT_ABA
    SPCM_FEAT_BASEXIO = SPCM_FEAT_BASEXIO
    SPCM_FEAT_AMPLIFIER_10V = SPCM_FEAT_AMPLIFIER_10V
    SPCM_FEAT_STARHUBSYSMASTER = SPCM_FEAT_STARHUBSYSMASTER
    SPCM_FEAT_DIFFMODE = SPCM_FEAT_DIFFMODE
    SPCM_FEAT_SEQUENCE = SPCM_FEAT_SEQUENCE
    SPCM_FEAT_AMPMODULE_10V = SPCM_FEAT_AMPMODULE_10V
    SPCM_FEAT_STARHUBSYSSLAVE = SPCM_FEAT_STARHUBSYSSLAVE
    SPCM_FEAT_NETBOX = SPCM_FEAT_NETBOX
    SPCM_FEAT_REMOTESERVER = SPCM_FEAT_REMOTESERVER
    SPCM_FEAT_SCAPP = SPCM_FEAT_SCAPP
    SPCM_FEAT_CUSTOMMOD_MASK = SPCM_FEAT_CUSTOMMOD_MASK


def decode_card_features(value: int) -> List[CardFeature]:
    possibe_values = [feature.value for feature in CardFeature]
    return [CardFeature(found_value) for found_value in _decode_bitmap_using_enum(value, possibe_values)]


class AdvancedCardFeature(Enum):
    SPCM_FEAT_EXTFW_SEGSTAT = SPCM_FEAT_EXTFW_SEGSTAT
    SPCM_FEAT_EXTFW_SEGAVERAGE = SPCM_FEAT_EXTFW_SEGAVERAGE
    SPCM_FEAT_EXTFW_BOXCAR = SPCM_FEAT_EXTFW_BOXCAR


def decode_advanced_card_features(value: int) -> List[AdvancedCardFeature]:
    possible_values = [feature.value for feature in AdvancedCardFeature]
    return [AdvancedCardFeature(found_value) for found_value in _decode_bitmap_using_enum(value, possible_values)]


def _decode_bitmap_using_enum(bitmap_value: int, test_values: List[int]) -> List[int]:
    possible_values = sorted(test_values)
    values_in_bitmap = list(
        filter(lambda x: x > 0, [possible_value & bitmap_value for possible_value in possible_values])
    )
    return values_in_bitmap


def error_handler(func: Callable) -> Callable:

    unreported_unraised_error_codes = {ERR_OK: "Execution OK, no error"}

    reported_unraised_error_codes: Dict[int, str] = {
        ERR_LASTERR: "Old error waiting to be read. Please read the full error information before proceeding. The "
        "driver is locked until the error information can be read.",
        ERR_TIMEOUT: "A timeout occurred while waiting for an interrupt.",
        ERR_ABORT: "Abort of wait function. The function has been aborted from another thread.",
    }

    known_raised_error_codes = {
        ERR_VALUE: "The value for this register is not in a valid range. The allowed values and ranges are listed in"
        "the board specific documentation.",
        ERR_INVALIDHANDLE: "The used handle is not valid.",
        ERR_SETUP: "The programmed setup for the card is not valid.",
        ERR_RUNNING: "The board is still running. this function is not available now or this register is not accessible"
        " now.",
    }

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        error_code = func(*args, **kwargs)
        if error_code in unreported_unraised_error_codes:
            pass
        elif error_code in reported_unraised_error_codes:
            print(
                f"Unraised spectrum error from {func.__name__}: {reported_unraised_error_codes[error_code]} "
                f"({error_code})"
            )
        elif error_code in known_raised_error_codes:
            raise SpectrumApiCallFailed(func.__name__, error_code, known_raised_error_codes[error_code])
        else:
            raise SpectrumApiCallFailed(func.__name__, error_code, f"command or value {args[1]}.")

    return wrapper


def get_spectrum_i32_api_param(device_handle: DEVICE_HANDLE_TYPE, spectrum_command: int) -> int:
    param = int32(0)
    error_handler(spcm_dwGetParam_i32)(device_handle, spectrum_command, byref(param))
    return param.value


def get_spectrum_i64_api_param(device_handle: DEVICE_HANDLE_TYPE, spectrum_command: int) -> int:
    param = int64(0)
    error_handler(spcm_dwGetParam_i64)(device_handle, spectrum_command, byref(param))
    return param.value


def set_spectrum_i32_api_param(device_handle: DEVICE_HANDLE_TYPE, spectrum_command: int, value: int) -> None:
    error_handler(spcm_dwSetParam_i32)(device_handle, spectrum_command, value)


def set_spectrum_i64_api_param(device_handle: DEVICE_HANDLE_TYPE, spectrum_command: int, value: int) -> None:
    error_handler(spcm_dwSetParam_i64)(device_handle, spectrum_command, value)


def set_transfer_buffer(device_handle: DEVICE_HANDLE_TYPE, buffer: TransferBuffer) -> None:
    error_handler(spcm_dwDefTransfer_i64)(
        device_handle,
        buffer.type.value,
        buffer.direction.value,
        buffer.notify_size_bytes,
        buffer.data_buffer_pointer,
        buffer.board_memory_offset_bytes,
        buffer.data_buffer_length_bytes,
    )


def spectrum_handle_factory(visa_string: str) -> DEVICE_HANDLE_TYPE:
    try:
        handle = DEVICE_HANDLE_TYPE(spcm_hOpen(create_string_buffer(bytes(visa_string, encoding="utf8"))))
    except RuntimeError as er:
        SpectrumIOError(f"Could not connect to Spectrum card: {er}")
    return handle


def destroy_handle(handle: DEVICE_HANDLE_TYPE) -> None:
    try:
        spcm_vClose(handle)
    except RuntimeError as er:
        SpectrumIOError(f"Could not disconnect from Spectrum card: {er}")


@dataclass
class AvailableIOModes:
    X0: EnumMeta
    X1: EnumMeta
    X2: EnumMeta
    X3: EnumMeta


def create_available_modes_enum_meta(available_modes: List[IOLineMode]) -> EnumMeta:
    return Enum("AvailableModes", {mode.name: mode.value for mode in available_modes})  # type: ignore
