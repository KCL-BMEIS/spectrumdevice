"""Provides classes defining the configuration of transfer buffers used to transfer data between a Spectrum card and a
PC. See the Spectrum documentation for more information. Also provides Enums defining the  settings used to configure
a transfer buffer."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.
from copy import copy
from ctypes import c_void_p
from dataclasses import dataclass
from enum import Enum

from numpy import ndarray, zeros, int16, uint8

from spectrumdevice.spectrum_wrapper import DEVICE_HANDLE_TYPE
from spectrumdevice.spectrum_wrapper.error_handler import error_handler

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
    from spectrumdevice.spectrum_wrapper.mock_pyspcm import (
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
    """A buffer for transferring samples between spectrumdevice software and a hardware device. See the 'Definition of the
    transfer buffer' section of the Spectrum documentation for more information. This implementation of the buffer
    sets the notify size equal to the acquisition length."""

    type: BufferType
    """Specifies whether the buffer is to be used to transfer samples, timestamps or A/B data."""
    direction: BufferDirection
    """Specifies whether the buffer is to be used to transfer data from the card to the PC, or the PC to the card."""
    board_memory_offset_bytes: int
    """Sets the offset for transfer in board memory. Typically 0. See Spectrum documentation for more information."""
    data_array: ndarray
    """1D numpy array into which samples will be written during transfer."""

    def copy_contents(self) -> ndarray:
        return copy(self.data_array)

    @property
    def data_array_pointer(self) -> c_void_p:
        """A pointer to the data array."""
        return self.data_array.ctypes.data_as(c_void_p)

    @property
    def data_array_length_in_bytes(self) -> int:
        """The length of the array into which sample will be written, in bytes."""
        return self.data_array.size * self.data_array.itemsize

    @property
    def notify_size_in_bytes(self) -> int:
        """The number of transferred bytes after which a notification of transfer is sent from the device. This is
        currently always set to the length of the data array, meaning that a notification will be received once the
        transfer is complete. See the Spectrum documentation for more information."""
        return self.data_array_length_in_bytes

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TransferBuffer):
            return (
                (self.type == other.type)
                and (self.direction == other.direction)
                and (self.board_memory_offset_bytes == other.board_memory_offset_bytes)
                and (self.data_array == other.data_array).all()
            )
        else:
            raise NotImplementedError()


class CardToPCDataTransferBuffer(TransferBuffer):
    """A TransferBuffer configured for card-to-pc transfer of samples (rather than timestamps or ABA data)."""

    def __init__(self, size_in_samples: int, board_memory_offset_bytes: int = 0) -> None:
        """
        Args:
            size_in_samples (int): The size of the array into which samples will be written, in samples.
            board_memory_offset_bytes (int): Sets the offset for transfer in board memory. Default 0. See Spectrum
                documentation for more information.
        """
        self.type = BufferType.SPCM_BUF_DATA
        self.direction = BufferDirection.SPCM_DIR_CARDTOPC
        self.board_memory_offset_bytes = board_memory_offset_bytes
        self.data_array = zeros(size_in_samples, int16)


class CardToPCTimestampTransferBuffer(TransferBuffer):
    def __init__(self) -> None:
        self.type = BufferType.SPCM_BUF_TIMESTAMP
        self.direction = BufferDirection.SPCM_DIR_CARDTOPC
        self.board_memory_offset_bytes = 0
        self.data_array: ndarray = zeros(4096, dtype=uint8)

    def copy_contents(self) -> ndarray:
        return copy(self.data_array[0::2])  # only every other item in the array has a timestamp written to it

    @property
    def notify_size_in_bytes(self) -> int:
        return 4096  # Timestamp buffer uses polling mode which requires the (ignored) notify size to be set to 4096


def set_transfer_buffer(device_handle: DEVICE_HANDLE_TYPE, buffer: TransferBuffer) -> None:
    error_handler(spcm_dwDefTransfer_i64)(
        device_handle,
        buffer.type.value,
        buffer.direction.value,
        buffer.notify_size_in_bytes,
        buffer.data_array_pointer,
        buffer.board_memory_offset_bytes,
        buffer.data_array_length_in_bytes,
    )
