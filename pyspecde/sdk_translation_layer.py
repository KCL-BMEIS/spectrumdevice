from ctypes import c_void_p, create_string_buffer, byref
from dataclasses import dataclass
from enum import Enum
from typing import NewType

from numpy import ndarray

from third_party.specde.py_header.regs import (
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
)

try:
    from third_party.specde.pyspcm import (
        SPCM_BUF_DATA,
        SPCM_BUF_ABA,
        SPCM_BUF_TIMESTAMP,
        SPCM_DIR_PCTOCARD,
        SPCM_DIR_CARDTOPC,
        spcm_hOpen,
        spcm_vClose,
        int32,
        spcm_dwGetParam_i32,
        spcm_dwGetParam_i64,
        int64,
        spcm_dwDefTransfer_i64,
    )
except OSError:
    from tests.mock_pyspcm import (
        SPCM_BUF_DATA,
        SPCM_BUF_ABA,
        SPCM_BUF_TIMESTAMP,
        SPCM_DIR_PCTOCARD,
        SPCM_DIR_CARDTOPC,
        spcm_hOpen,
        spcm_vClose,
        int32,
        spcm_dwGetParam_i32,
        spcm_dwGetParam_i64,
        int64,
        spcm_dwDefTransfer_i64,
    )

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
    card_handle: DEVICE_HANDLE_TYPE
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


class AcquisitionMode(Enum):
    SPC_REC_STD_SINGLE = SPC_REC_STD_SINGLE
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


def get_spectrum_i32_api_param(device_handle: DEVICE_HANDLE_TYPE, spectrum_command: int) -> int:
    param = int32(0)
    spcm_dwGetParam_i32(device_handle, spectrum_command, byref(param))
    return param.value


def get_spectrum_i64_api_param(device_handle: DEVICE_HANDLE_TYPE, spectrum_command: int) -> int:
    param = int64(0)
    spcm_dwGetParam_i64(device_handle, spectrum_command, byref(param))
    return param.value


def set_spectrum_i32_api_param(device_handle: DEVICE_HANDLE_TYPE, spectrum_command: int, value: int) -> None:
    spcm_dwGetParam_i32(device_handle, spectrum_command, value)


def set_spectrum_i64_api_param(device_handle: DEVICE_HANDLE_TYPE, spectrum_command: int, value: int) -> None:
    spcm_dwGetParam_i64(device_handle, spectrum_command, value)


def set_transfer_buffer(device_handle: DEVICE_HANDLE_TYPE, buffer: TransferBuffer) -> None:
    spcm_dwDefTransfer_i64(
        device_handle,
        buffer.type.value,
        buffer.direction.value,
        buffer.notify_size_bytes,
        buffer.data_buffer_pointer,
        buffer.board_memory_offset_bytes,
        buffer.data_buffer_length_bytes,
    )


def spectrum_handle_factory(visa_string: str) -> DEVICE_HANDLE_TYPE:
    return DEVICE_HANDLE_TYPE(spcm_hOpen(create_string_buffer(bytes(visa_string, encoding="utf8"))))


def destroy_handle(handle: DEVICE_HANDLE_TYPE) -> None:
    spcm_vClose(handle)
