"""Provides Pythonic functions for communicating with Spectrum hardware. The functions wrap the C-style Spectrum API."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

import logging
from ctypes import c_void_p, byref, create_string_buffer
from typing import NewType, List

from spectrumdevice.spectrum_wrapper.error_handler import error_handler
from spectrumdevice.exceptions import SpectrumIOError

logger = logging.getLogger(__name__)

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
    from spectrumdevice.spectrum_wrapper.mock_pyspcm import (
        spcm_dwSetParam_i32,
        spcm_dwSetParam_i64,
        spcm_hOpen,
        spcm_vClose,
        int32,
        spcm_dwGetParam_i32,
        spcm_dwGetParam_i64,
        int64,
    )

    logger.warning("Spectrum drivers not found. Hardware cannot be communicated with. Only Mock devices can be used.")
    SPECTRUM_DRIVERS_FOUND = False

DEVICE_HANDLE_TYPE = NewType("DEVICE_HANDLE_TYPE", c_void_p)


def decode_bitmap_using_list_of_ints(bitmap_value: int, test_values: List[int]) -> List[int]:
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
