from numpy import float_, iinfo, issubdtype, signedinteger, pi, sin, linspace, int_, ones
from numpy.typing import NDArray


def make_full_scale_sine_waveform(
    frequency_in_hz: float, sample_rate_in_hz: int, num_cycles: float, dtype: type
) -> tuple[NDArray[float_], NDArray[int_]]:
    if not issubdtype(dtype, signedinteger):
        raise ValueError("dtype must be a signed integer type")
    full_scale_max_value = iinfo(dtype).max
    duration = num_cycles / frequency_in_hz
    t = linspace(0, duration, int(duration * sample_rate_in_hz + 1))
    return t, (sin(2 * pi * frequency_in_hz * t) * full_scale_max_value).astype(dtype)


def make_full_scale_rect_waveform(
    sample_rate_in_hz: int, duration_in_seconds: float, dtype: type
) -> tuple[NDArray[float_], NDArray[int_]]:
    if not issubdtype(dtype, signedinteger):
        raise ValueError("dtype must be a signed integer type")
    duration_in_samples = int(duration_in_seconds * sample_rate_in_hz)
    full_scale_max_value = iinfo(dtype).max
    t = linspace(0, duration_in_samples - 1 / sample_rate_in_hz, duration_in_samples)
    return t, (ones(duration_in_samples) * full_scale_max_value).astype(dtype)
