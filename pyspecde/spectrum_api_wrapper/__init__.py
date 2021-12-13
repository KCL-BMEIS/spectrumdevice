from ctypes import c_void_p, create_string_buffer, byref
from enum import Enum
from typing import List, NewType

from pyspecde.exceptions import SpectrumIOError
from pyspecde.spectrum_api_wrapper.error_handler import error_handler
from spectrum_gmbh.regs import (
    SPC_REC_STD_SINGLE,
    SPC_REC_FIFO_MULTI,
    SPC_CM_INTPLL,
    SPC_REC_FIFO_SINGLE,
)

try:
    from spectrum_gmbh.pyspcm import (
        spcm_dwSetParam_i32,
        spcm_dwSetParam_i64,
        spcm_hOpen,
        spcm_vClose,
        int32,
        spcm_dwGetParam_i32,
        spcm_dwGetParam_i64,
        int64,
    )

    SPECTRUM_DRIVERS_FOUND = True
except OSError:
    from pyspecde.spectrum_api_wrapper.mock_pyspcm import (
        spcm_dwSetParam_i32,
        spcm_dwSetParam_i64,
        spcm_hOpen,
        spcm_vClose,
        int32,
        spcm_dwGetParam_i32,
        spcm_dwGetParam_i64,
        int64,
    )

    print("Spectrum drivers not found. Hardware cannot be communicated with. Tests can be run in MOCK_HARDWARE mode.")
    SPECTRUM_DRIVERS_FOUND = False

DEVICE_HANDLE_TYPE = NewType("DEVICE_HANDLE_TYPE", c_void_p)


class AcquisitionMode(Enum):
    SPC_REC_STD_SINGLE = SPC_REC_STD_SINGLE
    SPC_REC_FIFO_SINGLE = SPC_REC_FIFO_SINGLE
    SPC_REC_FIFO_MULTI = SPC_REC_FIFO_MULTI


class ClockMode(Enum):
    SPC_CM_INTPLL = SPC_CM_INTPLL


def _decode_bitmap_using_enum(bitmap_value: int, test_values: List[int]) -> List[int]:
    possible_values = sorted(test_values)
    values_in_bitmap = list(
        filter(lambda x: x > 0, [possible_value & bitmap_value for possible_value in possible_values])
    )
    return values_in_bitmap


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


def spectrum_handle_factory(visa_string: str) -> DEVICE_HANDLE_TYPE:  # type: ignore
    try:
        handle = DEVICE_HANDLE_TYPE(spcm_hOpen(create_string_buffer(bytes(visa_string, encoding="utf8"))))
        return handle
    except RuntimeError as er:
        SpectrumIOError(f"Could not connect to Spectrum card: {er}")


def destroy_handle(handle: DEVICE_HANDLE_TYPE) -> None:
    try:
        spcm_vClose(handle)
    except RuntimeError as er:
        SpectrumIOError(f"Could not disconnect from Spectrum card: {er}")
