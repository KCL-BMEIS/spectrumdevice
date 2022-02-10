from datetime import datetime
from dataclasses import dataclass

from numpy import ndarray


@dataclass
class Waveform:
    timestamp: datetime
    samples: ndarray
