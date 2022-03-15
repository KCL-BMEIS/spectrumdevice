from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

from numpy import float_
from numpy.typing import NDArray


@dataclass
class Measurement:
    waveforms: List[NDArray[float_]]
    timestamp: Optional[datetime]
