from numpy import float_, iinfo, issubdtype, signedinteger, pi, sin, linspace, int_
from numpy.typing import NDArray


def make_full_scale_sine_waveform(
    frequency_in_hz: float, sample_rate_hz: int, num_cycles: float, dtype: type
) -> tuple[NDArray[float_], NDArray[int_]]:
    if not issubdtype(dtype, signedinteger):
        raise ValueError("dtype must be a signed integer type")

    full_scale_max_value = iinfo(dtype).max
    duration = num_cycles / frequency_in_hz
    t = linspace(0, duration, int(duration * sample_rate_hz + 1))
    return t, (sin(2 * pi * frequency_in_hz * t) * full_scale_max_value).astype(dtype)
