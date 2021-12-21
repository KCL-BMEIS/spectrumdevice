from ctypes import c_void_p
from dataclasses import dataclass
from enum import Enum

from numpy import ndarray, zeros, int16

from pyspecde.spectrum_wrapper import DEVICE_HANDLE_TYPE
from pyspecde.spectrum_wrapper.error_handler import error_handler

try:
    from spectrum_gmbh.pyspcm import (
        SPCM_BUF_DATA,
        SPCM_BUF_ABA,
        SPCM_BUF_TIMESTAMP,
        SPCM_DIR_PCTOCARD,
        SPCM_DIR_CARDTOPC,
        spcm_dwDefTransfer_i64,
    )
except OSError:
    from pyspecde.spectrum_wrapper.mock_pyspcm import (
        SPCM_BUF_DATA,
        SPCM_BUF_ABA,
        SPCM_BUF_TIMESTAMP,
        SPCM_DIR_PCTOCARD,
        SPCM_DIR_CARDTOPC,
        spcm_dwDefTransfer_i64,
    )


class BufferType(Enum):
    """An Enum representing the three different types of transfer buffer. See the Spectrum documentation for more
    information."""

    SPCM_BUF_DATA = SPCM_BUF_DATA
    SPCM_BUF_ABA = SPCM_BUF_ABA
    SPCM_BUF_TIMESTAMP = SPCM_BUF_TIMESTAMP


class BufferDirection(Enum):
    """An Enum representing the two different directions of transfer undertaken by a transfer buffer. See the Spectrum
    documentation for more information."""

    SPCM_DIR_PCTOCARD = SPCM_DIR_PCTOCARD
    SPCM_DIR_CARDTOPC = SPCM_DIR_CARDTOPC


@dataclass
class TransferBuffer:
    """A buffer for transferring samples between pyspecde software and a hardware device. See the 'Definition of the
    transfer buffer' section of the Spectrum documentation for more information. This implementation of the buffer
    sets the notify size equal to the acquisition length."""

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


class CardToPCDataTransferBuffer(TransferBuffer):
    """A TransferBuffer configured for card-to-pc transfer of samples (rather than timestamps or ABA data)."""

    def __init__(self, size_in_samples: int, board_memory_offset_bytes: int = 0) -> None:
        self.type = BufferType.SPCM_BUF_DATA
        self.direction = BufferDirection.SPCM_DIR_CARDTOPC
        self.board_memory_offset_bytes = board_memory_offset_bytes
        self.data_buffer = zeros(size_in_samples, int16)


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
