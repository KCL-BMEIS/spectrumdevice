from datetime import datetime
from dataclasses import dataclass
from typing import List

from numpy import float_
from numpy.typing import NDArray


@dataclass
class Measurement:
    waveforms: List[NDArray[float_]]
    timestamp: datetime
