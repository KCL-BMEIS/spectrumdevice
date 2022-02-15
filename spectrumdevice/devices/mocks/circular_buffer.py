from dataclasses import dataclass
from typing import Optional

from numpy import ndarray, arange, bool_, uint64
from numpy.typing import NDArray


def _wrap_indices(indices: ndarray, array_size: int) -> ndarray:
    for i, index in enumerate(indices):
        indices[i] = _wrap_index(index, array_size)
    return indices


def _wrap_index(index: int, array_size: int) -> int:
    if index < array_size:
        return index
    else:
        return index - array_size


@dataclass
class WriteHead:
    last_write_pos: Optional[int]
    next_write_pos: int


def _write_to_circular_buffer(
    dest_buffer: NDArray[uint64],
    dest_buffer_free_status: NDArray[bool_],
    source_buffer: NDArray[uint64],
    start_index: int,
    source_buffer_free_status: Optional[Optional[NDArray[bool_]]] = None,
) -> WriteHead:

    if source_buffer_free_status is not None:
        source_indices_to_write = arange(len(source_buffer))[[not s for s in source_buffer_free_status]]
    else:
        source_indices_to_write = arange(len(source_buffer))
    n_elements_to_write = len(source_indices_to_write)

    if n_elements_to_write > 0:

        buffer_len = len(dest_buffer)
        num_free_elements_in_buffer = len(dest_buffer[dest_buffer_free_status])

        if n_elements_to_write > num_free_elements_in_buffer:
            raise MockCircularBufferOverrunError()

        write_indices = arange(n_elements_to_write + start_index)
        wrapped_write_indices = _wrap_indices(write_indices, buffer_len)

        for source_index, destination_index in zip(source_indices_to_write, wrapped_write_indices):
            dest_buffer[destination_index] = source_buffer[source_index]
            if source_buffer_free_status is not None:
                source_buffer_free_status[source_index] = True
            dest_buffer_free_status[destination_index] = False

        last_index_written = wrapped_write_indices[-1]
        return WriteHead(
            last_write_pos=last_index_written, next_write_pos=_wrap_index(last_index_written + 1, buffer_len)
        )

    else:
        return WriteHead(last_write_pos=None, next_write_pos=start_index)


class MockCircularBufferOverrunError(Exception):
    pass
