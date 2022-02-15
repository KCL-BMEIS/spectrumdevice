from datetime import datetime
from dataclasses import dataclass

from numpy import float_
from numpy.typing import NDArray


@dataclass
class Waveform:
    timestamp: datetime
    samples: NDArray[float_]
