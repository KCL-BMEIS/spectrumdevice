"""Spectrum driver mocking.

If spectrum drivers are not found, this file is imported instead of spectrum_gmhb/pyspcm.py. It mocks the essential
components of pyspcm.py, preventing spectrumdevice from failing while importing pyspcm.py. Mock devices can then be used to
test spectrumdevice software. The functions and variables here aren't actually called by the mock devices, only imported.
"""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

import platform
import ctypes
from typing import Any

oPlatform = platform.architecture()
if oPlatform[0] == "64bit":
    bIs64Bit = 1
else:
    bIs64Bit = 0

# define card handle type
if bIs64Bit:
    # for unknown reasons c_void_p gets messed up on Win7/64bit, but this works:
    drv_handle = ctypes.POINTER(ctypes.c_uint64)
else:
    drv_handle = ctypes.c_void_p  # type: ignore

int32 = ctypes.c_int32
int64 = ctypes.c_int64

SPCM_DIR_PCTOCARD = 0
SPCM_DIR_CARDTOPC = 1

SPCM_BUF_DATA = 1000  # main data buffer for acquired or generated samples
SPCM_BUF_ABA = 2000  # buffer for ABA data, holds the A-DATA (slow samples)
SPCM_BUF_TIMESTAMP = 3000  # buffer for timestamps


def spcm_dwGetParam_i32(handle: ctypes.c_void_p, command: int, value: Any) -> None:
    pass


def spcm_dwSetParam_i32(handle: ctypes.c_void_p, command: int, value: int) -> None:
    pass


def spcm_dwGetParam_i64(handle: ctypes.c_void_p, command: int, value: Any) -> None:
    pass


def spcm_dwSetParam_i64(handle: ctypes.c_void_p, command: int, value: int) -> None:
    pass


def spcm_hOpen(string_buffer: ctypes.c_char_p) -> ctypes.c_void_p:
    pass


def spcm_vClose(handle: ctypes.c_void_p) -> None:
    pass


def spcm_dwDefTransfer_i64(
    handle: ctypes.c_void_p,
    buffer_type: int,
    direction: int,
    notify_size: int,
    buffer_pointer: ctypes.c_void_p,
    offset: int,
    length: int,
) -> int:
    pass
