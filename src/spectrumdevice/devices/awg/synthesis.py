from numpy import float_, iinfo, issubdtype, signedinteger, pi, sin, linspace, int_, ones, int16
from numpy.typing import NDArray


def make_full_scale_sine_waveform(
    frequency_in_hz: float, sample_rate_in_hz: int, num_cycles: float, dtype: type = int16
) -> tuple[NDArray[float_], NDArray[int_]]:
    """Create a sine waveform covering the full range of the given data type. The resulting waveform is intended to
    be transferred to the AWG's on-board memory for generation.

    Args:
        frequency_in_hz (float): The frequency of the sine waveform in Hz
        sample_rate_in_hz (int): The sampling rate of the waveform to synthesise. Make sure your card is set to the
            same sampler rate.
        num_cycles (int): The number of sinusoidal cycles to synthesise.
        dtype (type): Signed integer type to use. Default int16.
    """
    if not issubdtype(dtype, signedinteger):
        raise ValueError("dtype must be a signed integer type")
    full_scale_max_value = iinfo(dtype).max
    duration = num_cycles / frequency_in_hz
    t = linspace(0, duration, int(duration * sample_rate_in_hz + 1))
    return t, (sin(2 * pi * frequency_in_hz * t) * full_scale_max_value).astype(dtype)


def make_full_scale_rect_waveform(
    sample_rate_in_hz: int, duration_in_seconds: float, dtype: type = int16
) -> tuple[NDArray[float_], NDArray[int_]]:
    """Create a rectangular waveform covering the full range of the given data type. The resulting waveform is intended
    to be transferred to the AWG's on-board memory for generation.

    Args:
        sample_rate_in_hz (int): The sampling rate of the waveform to synthesise. Make sure your card is set to the
            same sampler rate.
        duration_in_seconds (float): The duration of the rectangular waveform in seconds.
        dtype (type): Signed integer type to use. Default int16.
    """
    if not issubdtype(dtype, signedinteger):
        raise ValueError("dtype must be a signed integer type")
    duration_in_samples = int(duration_in_seconds * sample_rate_in_hz)
    full_scale_max_value = iinfo(dtype).max
    t = linspace(0, duration_in_samples - 1 / sample_rate_in_hz, duration_in_samples)
    return t, (ones(duration_in_samples) * full_scale_max_value).astype(dtype)
