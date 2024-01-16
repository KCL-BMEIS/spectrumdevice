from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from spectrumdevice.settings import SpectrumRegisterLength
from spectrumdevice.settings.pulse_generator import (
    PulseGeneratorMultiplexerTriggerSource,
    PulseGeneratorOutputSettings,
    PulseGeneratorTriggerDetectionMode,
    PulseGeneratorTriggerMode,
    PulseGeneratorTriggerSettings,
)

MultiplexerTriggerSourceTypeVar = TypeVar(
    "MultiplexerTriggerSourceTypeVar", bound=PulseGeneratorMultiplexerTriggerSource
)


class PulseGeneratorMultiplexerInterface(Generic[MultiplexerTriggerSourceTypeVar], ABC):
    @property
    @abstractmethod
    def number(self) -> int:
        raise NotImplementedError()

    def read_parent_device_register(
        self, spectrum_register: int, length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO
    ) -> int:
        raise NotImplementedError()

    def write_to_parent_device_register(
        self,
        spectrum_register: int,
        value: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> None:
        raise NotImplementedError()

    @property
    def output_inversion(self) -> bool:
        raise NotImplementedError()

    def set_output_inversion(self, inverted: bool) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def trigger_source(self) -> MultiplexerTriggerSourceTypeVar:
        raise NotImplementedError()

    @abstractmethod
    def set_trigger_source(self, trigger_source: MultiplexerTriggerSourceTypeVar) -> None:
        raise NotImplementedError()


class PulseGeneratorInterface(ABC):
    @abstractmethod
    def configure_output(self, settings: PulseGeneratorOutputSettings) -> None:
        raise NotImplementedError()

    @abstractmethod
    def configure_trigger(self, settings: PulseGeneratorTriggerSettings) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def number(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def read_parent_device_register(
        self, spectrum_register: int, length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO
    ) -> int:
        raise NotImplementedError()

    @abstractmethod
    def write_to_parent_device_register(
        self,
        spectrum_register: int,
        value: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def multiplexer_1(self) -> PulseGeneratorMultiplexerInterface:
        raise NotImplementedError()

    @property
    @abstractmethod
    def multiplexer_2(self) -> PulseGeneratorMultiplexerInterface:
        raise NotImplementedError()

    @property
    @abstractmethod
    def clock_rate_in_hz(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def clock_period_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def enabled(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def enable(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def disable(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def output_inversion(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def set_output_inversion(self, inverted: bool) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def trigger_detection_mode(self) -> PulseGeneratorTriggerDetectionMode:
        raise NotImplementedError()

    @abstractmethod
    def set_trigger_detection_mode(self, mode: PulseGeneratorTriggerDetectionMode) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def trigger_mode(self) -> PulseGeneratorTriggerMode:
        raise NotImplementedError()

    @abstractmethod
    def set_trigger_mode(self, mode: PulseGeneratorTriggerMode) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def min_allowed_period_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def max_allowed_period_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def allowed_period_step_size_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def period_in_seconds(self) -> float:
        raise NotImplementedError()

    @abstractmethod
    def set_period_in_seconds(self, period: float, coerce: bool = True) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def min_allowed_high_voltage_duration_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def max_allowed_high_voltage_duration_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def allowed_high_voltage_duration_step_size_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def duration_of_high_voltage_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def duration_of_low_voltage_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def duty_cycle(self) -> float:
        raise NotImplementedError()

    @abstractmethod
    def set_duty_cycle(self, duty_cycle: float, coerce: bool = True) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def min_allowed_pulses(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def max_allowed_pulses(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def allowed_num_pulses_step_size(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def num_pulses(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_num_pulses(self, num_pulses: int, coerce: bool = True) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def min_allowed_delay_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def max_allowed_delay_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def allowed_delay_step_size_in_seconds(self) -> float:
        raise NotImplementedError()

    @property
    @abstractmethod
    def delay_in_seconds(self) -> float:
        raise NotImplementedError()

    @abstractmethod
    def set_delay_in_seconds(self, delay_in_seconds: float, coerce: bool = True) -> float:
        raise NotImplementedError()
