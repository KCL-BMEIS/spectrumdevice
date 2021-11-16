import platform
import ctypes

oPlatform = platform.architecture()
if oPlatform[0] == '64bit':
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


def spcm_dwGetParam_i32() -> None:
    pass


def spcm_dwSetParam_i32() -> None:
    pass


def spcm_dwSetParam_i64() -> None:
    pass


def spcm_dwGetParam_i64() -> None:
    pass


def spcm_hOpen() -> None:
    pass


def spcm_vClose() -> None:
    pass
