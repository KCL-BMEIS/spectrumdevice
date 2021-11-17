from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from third_party.specde.py_header.regs import (
    SPC_REC_STD_SINGLE,
    SPC_REC_FIFO_MULTI,
    SPC_TMASK_SOFTWARE,
    SPC_TMASK_EXT0,
    SPC_CM_INTPLL,
    CHANNEL0,
    CHANNEL1,
    CHANNEL2,
    CHANNEL3,
    CHANNEL4,
    CHANNEL5,
    CHANNEL6,
    CHANNEL7,
    CHANNEL8,
    CHANNEL9,
    CHANNEL10,
    CHANNEL11,
    CHANNEL12,
    CHANNEL13,
    CHANNEL14,
    CHANNEL15,
    SPC_AMP1,
    SPC_AMP2,
    SPC_AMP3,
    SPC_AMP4,
    SPC_AMP5,
    SPC_AMP6,
    SPC_AMP7,
    SPC_AMP8,
    SPC_AMP11,
    SPC_AMP10,
    SPC_AMP9,
    SPC_AMP12,
    SPC_AMP13,
    SPC_AMP14,
    SPC_AMP15,
    SPC_AMP0,
    SPC_OFFS0,
    SPC_OFFS1,
    SPC_OFFS2,
    SPC_OFFS3,
    SPC_OFFS4,
    SPC_OFFS5,
    SPC_OFFS7,
    SPC_OFFS6,
    SPC_OFFS8,
    SPC_OFFS9,
    SPC_OFFS10,
    SPC_OFFS11,
    SPC_OFFS12,
    SPC_OFFS13,
    SPC_OFFS14,
    SPC_OFFS15,
)


class AcquisitionMode(Enum):
    SPC_REC_STD_SINGLE = SPC_REC_STD_SINGLE
    SPC_REC_FIFO_MULTI = SPC_REC_FIFO_MULTI


class TriggerSource(Enum):
    SPC_TMASK_SOFTWARE = SPC_TMASK_SOFTWARE
    SPC_TMASK_EXT0 = SPC_TMASK_EXT0


class ClockMode(Enum):
    SPC_CM_INTPLL = SPC_CM_INTPLL


class SpectrumChannelName(Enum):
    CHANNEL0 = CHANNEL0
    CHANNEL1 = CHANNEL1
    CHANNEL2 = CHANNEL2
    CHANNEL3 = CHANNEL3
    CHANNEL4 = CHANNEL4
    CHANNEL5 = CHANNEL5
    CHANNEL6 = CHANNEL6
    CHANNEL7 = CHANNEL7
    CHANNEL8 = CHANNEL8
    CHANNEL9 = CHANNEL9
    CHANNEL10 = CHANNEL10
    CHANNEL11 = CHANNEL11
    CHANNEL12 = CHANNEL12
    CHANNEL13 = CHANNEL13
    CHANNEL14 = CHANNEL14
    CHANNEL15 = CHANNEL15


VERTICAL_RANGE_COMMANDS = (
    SPC_AMP0,
    SPC_AMP1,
    SPC_AMP2,
    SPC_AMP3,
    SPC_AMP4,
    SPC_AMP5,
    SPC_AMP6,
    SPC_AMP7,
    SPC_AMP8,
    SPC_AMP9,
    SPC_AMP10,
    SPC_AMP11,
    SPC_AMP12,
    SPC_AMP13,
    SPC_AMP14,
    SPC_AMP15,
)

VERTICAL_OFFSET_COMMANDS = (
    SPC_OFFS0,
    SPC_OFFS1,
    SPC_OFFS2,
    SPC_OFFS3,
    SPC_OFFS4,
    SPC_OFFS5,
    SPC_OFFS6,
    SPC_OFFS7,
    SPC_OFFS8,
    SPC_OFFS9,
    SPC_OFFS10,
    SPC_OFFS11,
    SPC_OFFS12,
    SPC_OFFS13,
    SPC_OFFS14,
    SPC_OFFS15,
)


class SpectrumChannelInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> SpectrumChannelName:
        raise NotImplementedError

    @property  # type: ignore
    @abstractmethod
    def enabled(self) -> bool:
        raise NotImplementedError

    @enabled.setter  # type: ignore
    @abstractmethod
    def enabled(self, enabled: bool) -> None:
        raise NotImplementedError

    @property  # type: ignore
    @abstractmethod
    def vertical_range_mv(self) -> int:
        raise NotImplementedError()

    @vertical_range_mv.setter  # type: ignore
    @abstractmethod
    def vertical_range_mv(self, vertical_range: int) -> int:
        raise NotImplementedError()

    @property  # type: ignore
    @abstractmethod
    def vertical_offset_percent(self) -> int:
        raise NotImplementedError()

    @vertical_offset_percent.setter  # type: ignore
    @abstractmethod
    def vertical_offset_percent(self, offset: int) -> int:
        raise NotImplementedError()


class SpectrumIntLengths(Enum):
    THIRTY_TWO = 0
    SIXTY_FOUR = 1


class SpectrumInterface(ABC):
    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def apply_channel_enabling(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def channels(self) -> List[SpectrumChannelInterface]:
        raise NotImplementedError()

    @property  # type: ignore
    @abstractmethod
    def acquisition_length_bytes(self) -> int:
        raise NotImplementedError()

    @acquisition_length_bytes.setter  # type: ignore
    @abstractmethod
    def acquisition_length_bytes(self, length_in_bytes: int) -> None:
        raise NotImplementedError()

    @property  # type: ignore
    @abstractmethod
    def post_trigger_length_bytes(self) -> int:
        raise NotImplementedError()

    @post_trigger_length_bytes.setter  # type: ignore
    @abstractmethod
    def post_trigger_length_bytes(self, length_in_bytes: int) -> None:
        raise NotImplementedError()

    @property  # type: ignore
    @abstractmethod
    def acquisition_mode(self) -> AcquisitionMode:
        raise NotImplementedError()

    @acquisition_mode.setter  # type: ignore
    @abstractmethod
    def acquisition_mode(self, mode: AcquisitionMode) -> None:
        raise NotImplementedError()

    @property  # type: ignore
    @abstractmethod
    def timeout_ms(self) -> int:
        raise NotImplementedError()

    @timeout_ms.setter  # type: ignore
    @abstractmethod
    def timeout_ms(self, timeout_in_ms: int) -> None:
        raise NotImplementedError()

    @property  # type: ignore
    @abstractmethod
    def trigger_sources(self) -> List[TriggerSource]:
        raise NotImplementedError()

    @trigger_sources.setter  # type: ignore
    @abstractmethod
    def trigger_sources(self, source: List[TriggerSource]) -> None:
        raise NotImplementedError()

    @property  # type: ignore
    @abstractmethod
    def clock_mode(self) -> ClockMode:
        raise NotImplementedError()

    @clock_mode.setter  # type: ignore
    @abstractmethod
    def clock_mode(self, mode: ClockMode) -> None:
        raise NotImplementedError()

    @property  # type: ignore
    @abstractmethod
    def sample_rate_hz(self) -> int:
        raise NotImplementedError()

    @sample_rate_hz.setter  # type: ignore
    @abstractmethod
    def sample_rate_hz(self, rate: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def set_spectrum_api_param(
        self,
        spectrum_command: int,
        value: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_spectrum_api_param(
        self,
        spectrum_command: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> int:
        raise NotImplementedError()
