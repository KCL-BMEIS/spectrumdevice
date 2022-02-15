from dataclasses import dataclass
from typing import Optional

from numpy import arange, bool_, uint64, take
from numpy.typing import NDArray


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
    """Mocks the operation of a spectrum device's buffer writing. Used to mock the writing of timestamps into on-board
    memory as well as the transfer of timestamps from on board memory into a transfer buffer."""

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

        all_buffer_indices = arange(buffer_len)
        write_indices = arange(n_elements_to_write + start_index)
        wrapped_write_indices = take(all_buffer_indices, write_indices, mode="wrap")

        for source_index, destination_index in zip(source_indices_to_write, wrapped_write_indices):
            dest_buffer[destination_index] = source_buffer[source_index]
            if source_buffer_free_status is not None:
                source_buffer_free_status[source_index] = True
            dest_buffer_free_status[destination_index] = False

        last_index_written = wrapped_write_indices[-1]
        return WriteHead(
            last_write_pos=last_index_written,
            next_write_pos=take(all_buffer_indices, last_index_written + 1, mode="wrap"),
        )

    else:
        return WriteHead(last_write_pos=None, next_write_pos=start_index)


class MockCircularBufferOverrunError(Exception):
    pass
