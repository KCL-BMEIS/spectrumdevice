"""Provides classes defining the configuration of transfer buffers used to transfer data between a Spectrum card and a
PC. See the Spectrum documentation for more information. Also provides Enums defining the  settings used to configure
a transfer buffer."""
from abc import ABC, abstractmethod

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.
from copy import copy
from ctypes import c_void_p
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Optional

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


SAMPLE_DATA_TYPE = int16


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
class TransferBuffer(ABC):
    """A buffer for transferring samples between spectrumdevice software and a hardware device. See the 'Definition of the
    transfer buffer' section of the Spectrum documentation for more information. This implementation of the buffer
    sets the notify-size equal to the acquisition length."""

    type: BufferType
    """Specifies whether the buffer is to be used to transfer samples, timestamps or A/B data."""
    direction: BufferDirection
    """Specifies whether the buffer is to be used to transfer data from the card to the PC, or the PC to the card."""
    board_memory_offset_bytes: int
    """Sets the offset for transfer in board memory. Typically 0. See Spectrum documentation for more information."""
    data_array: ndarray
    """1D numpy array into which samples will be written during transfer."""
    notify_size_in_pages: float
    """The number of transferred pages (4096 bytes) after which a notification of transfer is sent from the device."""

    @abstractmethod
    def read_chunk(self, chunk_position_in_bytes: int, chunk_size_in_bytes: int) -> ndarray:
        raise NotImplementedError()

    @abstractmethod
    def copy_contents(self) -> ndarray:
        raise NotImplementedError()

    @property
    def data_array_pointer(self) -> c_void_p:
        """A pointer to the data array."""
        return self.data_array.ctypes.data_as(c_void_p)

    @property
    def data_array_length_in_bytes(self) -> int:
        """The length of the array into which sample will be written, in bytes."""
        return self.data_array.size * self.data_array.itemsize

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


class SamplesTransferBuffer(TransferBuffer):
    def __init__(
        self,
        direction: BufferDirection,
        board_memory_offset_bytes: int,
        data_array: ndarray,
        notify_size_in_pages: float = 1,
    ) -> None:
        super().__init__(
            BufferType.SPCM_BUF_DATA, direction, board_memory_offset_bytes, data_array, notify_size_in_pages
        )

    def read_chunk(self, chunk_position_in_bytes: int, chunk_size_in_bytes: int) -> ndarray:
        chunk_position_in_samples = chunk_position_in_bytes // self.data_array.itemsize
        chunk_size_in_samples = chunk_size_in_bytes // self.data_array.itemsize
        return self.data_array[chunk_position_in_samples : chunk_position_in_samples + chunk_size_in_samples]

    def copy_contents(self) -> ndarray:
        return copy(self.data_array)


class TimestampsTransferBuffer(TransferBuffer):
    def __init__(self, direction: BufferDirection, board_memory_offset_bytes: int) -> None:
        # Timestamp buffer uses polling mode which requires the (ignored) notify size to be set to the page size
        super().__init__(
            BufferType.SPCM_BUF_TIMESTAMP,
            direction,
            board_memory_offset_bytes,
            zeros(NOTIFY_SIZE_PAGE_SIZE_IN_BYTES, dtype=uint8),
            NOTIFY_SIZE_PAGE_SIZE_IN_BYTES,
        )

    def read_chunk(self, chunk_position_in_bytes: int, chunk_size_in_bytes: int) -> ndarray:
        raise NotImplementedError("Reading a chunk is not implemented for TimestampsTransferBuffers.")

    def copy_contents(self) -> ndarray:
        return copy(self.data_array[0::2])  # only every other item in the array has a timestamp written to it


def transfer_buffer_factory(
    buffer_type: BufferType,
    direction: BufferDirection,
    size_in_samples: Optional[int] = None,
    board_memory_offset_bytes: int = 0,
    notify_size_in_pages: float = 1,
) -> "TransferBuffer":
    """
    Args:
        buffer_type (BufferType): Specifies whether the buffer is to be used to transfer samples, timestamps or A/B data.
        direction (BufferDirection): Specifies whether the buffer is to be used to transfer data from the card to the
            PC, or the PC to the card.
        size_in_samples (int): The size of the array into which samples will be written, in samples. Currently only
            required for BufferType.SPCM_BUF_DATA as SPCM_BUF_TIMESTAMP buffers are always 4096 uint8 long.
        board_memory_offset_bytes (int): Sets the offset for transfer in board memory. Default 0. See Spectrum
            documentation for more information.
        notify_size_in_pages (int): For BufferType.SPCM_BUF_DATA. The number of transferred pages (i.e. 4096 bytes)
        after which a notification of transfer is sent from the device, and therefore a chunk of samples is downloaded.
        See the Spectrum documentation for more information. Ignored for BufferType.SPCM_BUF_TIMESTAMP.
    """

    # _check_notify_size_validity(notify_size_in_pages)

    if buffer_type == BufferType.SPCM_BUF_DATA:
        if size_in_samples is not None:
            return SamplesTransferBuffer(
                direction, board_memory_offset_bytes, zeros(size_in_samples, SAMPLE_DATA_TYPE), notify_size_in_pages
            )
        else:
            raise ValueError("You must provide a buffer size_in_samples to create a BufferType.SPCM_BUF_DATA buffer.")
    elif buffer_type == BufferType.SPCM_BUF_TIMESTAMP:
        return TimestampsTransferBuffer(direction, board_memory_offset_bytes)
    else:
        raise NotImplementedError(f"TransferBuffer type {buffer_type} not yet supported.")


def _check_notify_size_validity(notify_size_in_pages: float) -> None:

    if notify_size_in_pages == 0:
        return

    notify_size_is_an_invalid_fraction_less_than_1 = (notify_size_in_pages < 1) and (
        notify_size_in_pages not in ALLOWED_FRACTIONAL_NOTIFY_SIZES_IN_PAGES
    )
    notify_size_greater_than_1_and_not_int = (notify_size_in_pages > 1) and (
        notify_size_in_pages != round(notify_size_in_pages)
    )
    notify_size_is_invalid = notify_size_is_an_invalid_fraction_less_than_1 or notify_size_greater_than_1_and_not_int

    if notify_size_is_invalid:
        raise ValueError(
            f"notify_size_in_pages must be an integer or one of the following fractional values "
            f"{ALLOWED_FRACTIONAL_NOTIFY_SIZES_IN_PAGES}"
        )


create_samples_acquisition_transfer_buffer = partial(
    transfer_buffer_factory, BufferType.SPCM_BUF_DATA, BufferDirection.SPCM_DIR_CARDTOPC
)

create_timestamp_acquisition_transfer_buffer = partial(
    transfer_buffer_factory, BufferType.SPCM_BUF_TIMESTAMP, BufferDirection.SPCM_DIR_CARDTOPC
)


def set_transfer_buffer(device_handle: DEVICE_HANDLE_TYPE, buffer: TransferBuffer) -> None:
    error_handler(spcm_dwDefTransfer_i64)(
        device_handle,
        buffer.type.value,
        buffer.direction.value,
        int(buffer.notify_size_in_pages * NOTIFY_SIZE_PAGE_SIZE_IN_BYTES),
        buffer.data_array_pointer,
        buffer.board_memory_offset_bytes,
        buffer.data_array_length_in_bytes,
    )


DEFAULT_NOTIFY_SIZE_IN_PAGES = 10
NOTIFY_SIZE_PAGE_SIZE_IN_BYTES = 4096
ALLOWED_FRACTIONAL_NOTIFY_SIZES_IN_PAGES = [1 / 2, 1 / 4, 1 / 8, 1 / 16, 1 / 32, 1 / 64, 1 / 128, 1 / 256]
