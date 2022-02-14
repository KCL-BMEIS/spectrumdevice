from typing import Optional, cast

from numpy import ndarray, arange


def _wrap_indices(indices: ndarray, array_size: int) -> ndarray:
    for i, index in enumerate(indices):
        indices[i] = _wrap_index(index, array_size)
    return indices


def _wrap_index(index: int, array_size: int) -> int:
    if index < array_size:
        return index
    else:
        return index - array_size


def _write_to_circular_buffer(
    dest_buffer: ndarray,
    dest_buffer_free_status: ndarray,
    source_buffer: ndarray,
    start_index: int,
    source_buffer_free_status: Optional[ndarray] = None,
) -> int:

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
        return cast(int, last_index_written)

    else:
        raise ValueError("No data to write")


class MockCircularBufferOverrunError(Exception):
    pass
