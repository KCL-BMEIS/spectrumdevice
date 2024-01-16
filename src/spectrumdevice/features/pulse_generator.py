from numpy import clip

from spectrum_gmbh.py_header.regs import SPC_XIO_PULSEGEN_AVAILLEN_MAX, SPC_XIO_PULSEGEN_AVAILLEN_MIN, \
    SPC_XIO_PULSEGEN_AVAILLEN_STEP, SPC_XIO_PULSEGEN_AVAILLOOPS_MAX, SPC_XIO_PULSEGEN_AVAILLOOPS_MIN, \
    SPC_XIO_PULSEGEN_AVAILLOOPS_STEP, SPC_XIO_PULSEGEN_CLOCK, SPC_XIO_PULSEGEN_ENABLE
from spectrumdevice.devices.abstract_device.interfaces import SpectrumIOLineInterface
from spectrumdevice.exceptions import SpectrumInvalidParameterValue
from spectrumdevice.settings.pulse_generator import PULSE_GEN_DELAY_COMMANDS, PULSE_GEN_ENABLE_COMMANDS, \
    PULSE_GEN_PULSE_PERIOD_COMMANDS, \
    PULSE_GEN_HIGH_DURATION_COMMANDS, PULSE_GEN_NUM_REPEATS_COMMANDS, decode_enabled_pulse_gens


class PulseGenerator:
    def __init__(self, parent: SpectrumIOLineInterface):
        self._parent_io_line = parent
        # last char of IO line name is IO line chanel number, which is used to set pulse generator number
        self._number = parent.name.name[-1]

    def _convert_clock_cycles_to_seconds(self, clock_cycles: int) -> float:
        return clock_cycles * self.clock_period_in_seconds

    def _convert_seconds_to_clock_cycles(self, seconds: float) -> float:
        return seconds * self.clock_rate_in_hz

    def _get_enabled_pulse_generator_ids(self) -> list[int]:
        return decode_enabled_pulse_gens(
            self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_ENABLE)
        )

    @property
    def clock_rate_in_hz(self) -> int:
        return self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_CLOCK)

    @property
    def clock_period_in_seconds(self) -> float:
        return 1 / self.clock_rate_in_hz

    @property
    def enabled(self) -> bool:
        return PULSE_GEN_ENABLE_COMMANDS(self._number) in self._get_enabled_pulse_generator_ids()

    def enable(self) -> None:
        currently_enabled_pulse_generators = self._get_enabled_pulse_generator_ids()
        if PULSE_GEN_ENABLE_COMMANDS(self._number) not in currently_enabled_pulse_generators:
            or_of_all_enabled = PULSE_GEN_ENABLE_COMMANDS(self._number) | currently_enabled_pulse_generators
            self._parent_io_line.write_to_parent_device_register(SPC_XIO_PULSEGEN_ENABLE, or_of_all_enabled)

    def disable(self) -> None:
        current_register_value = self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_ENABLE)
        if PULSE_GEN_ENABLE_COMMANDS(self._number) & current_register_value:
            self._parent_io_line.write_to_parent_device_register(
                current_register_value & ~PULSE_GEN_ENABLE_COMMANDS(self._number)
            )

    @property
    def min_allowed_period_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_MIN)
        )

    @property
    def max_allowed_period_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_MAX)
        )

    @property
    def _allowed_period_step_size_in_clock_cycles(self) -> int:
        return self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_STEP)

    @property
    def allowed_period_step_size_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self._allowed_period_step_size_in_clock_cycles
        )

    @property
    def period_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self._parent_io_line.read_parent_device_register(PULSE_GEN_PULSE_PERIOD_COMMANDS(self._number))
        )

    def set_period_in_seconds(self, period: float, coerce: bool = True) -> None:
        """ Set the time between the start of each generated pulse in seconds. If coerce is True, the requested value
        will be coerced according to min_allowed_period_in_seconds, max_allowed_period_in_seconds and
        allowed_period_step_size_in_seconds. Otherwise, when an invalid value is requested a
        SpectrumInvalidParameterValue will be raised. The allowed values are affected by the number of active
        channels and the sample rate."""
        period_in_clock_cycles = self._convert_seconds_to_clock_cycles(period)
        coerced_period = _coerce_fractional_value_to_allowed_integer(
            period_in_clock_cycles,
            int(self._convert_seconds_to_clock_cycles(self.min_allowed_period_in_seconds)),
            int(self._convert_seconds_to_clock_cycles(self.max_allowed_period_in_seconds)),
            self._allowed_period_step_size_in_clock_cycles
        )
        if not coerce and coerced_period != period:
            raise SpectrumInvalidParameterValue("pulse generator period",
                                                period_in_clock_cycles,
                                                self.min_allowed_period_in_seconds,
                                                self.max_allowed_period_in_seconds,
                                                self.allowed_period_step_size_in_seconds)

        self._parent_io_line.write_to_parent_device_register(
            PULSE_GEN_PULSE_PERIOD_COMMANDS(int(coerced_period))
        )

    @property
    def min_allowed_high_voltage_duration_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_MIN)
        )

    @property
    def max_allowed_high_voltage_duration_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_MAX)
        )

    @property
    def _allowed_high_voltage_duration_step_size_in_clock_cycles(self) -> int:
        return self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_STEP)

    @property
    def allowed_high_voltage_duration_step_size_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self._allowed_period_step_size_in_clock_cycles
        )

    @property
    def duration_of_high_voltage_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self._parent_io_line.read_parent_device_register(PULSE_GEN_HIGH_DURATION_COMMANDS(self._number))
        )

    @property
    def duration_of_low_voltage_in_seconds(self) -> float:
        return self.period_in_seconds - self.duration_of_high_voltage_in_seconds

    @property
    def duty_cycle(self) -> float:
        return self.duration_of_high_voltage_in_seconds / self.period_in_seconds

    def set_duty_cycle(self, duty_cycle: float, coerce: bool = True) -> float:
        """ Set the duty cycle. If coerce is True, the requested value will be coerced to be within allowed range and
        use allowed step size and then the coerced value wll be returned. Otherwise, when an invalid value is requested
        an SpectrumInvalidParameterValue will be raised. The allowed values are affected by the number of active
        channels and the sample rate.
        """
        requested_high_v_duration_in_clock_cycles = self._convert_seconds_to_clock_cycles(
            self.period_in_seconds * duty_cycle
        )
        clipped_duration = _coerce_fractional_value_to_allowed_integer(
            requested_high_v_duration_in_clock_cycles,
            int(self._convert_seconds_to_clock_cycles(self.min_allowed_high_voltage_duration_in_seconds)),
            int(self._convert_seconds_to_clock_cycles(self.max_allowed_high_voltage_duration_in_seconds)),
            self._allowed_high_voltage_duration_step_size_in_clock_cycles
        )
        if not coerce and clipped_duration != requested_high_v_duration_in_clock_cycles:
            raise SpectrumInvalidParameterValue("high-voltage duration",
                                                duty_cycle,
                                                self.min_allowed_high_voltage_duration_in_seconds,
                                                self.max_allowed_high_voltage_duration_in_seconds,
                                                self._allowed_high_voltage_duration_step_size_in_clock_cycles)
        self._parent_io_line.write_to_parent_device_register(
            PULSE_GEN_HIGH_DURATION_COMMANDS(self._number), clipped_duration
        )
        return self._convert_clock_cycles_to_seconds(clipped_duration) / self.period_in_seconds

    @property
    def min_allowed_pulses(self) -> int:
        return self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLOOPS_MIN)

    @property
    def max_allowed_pulses(self) -> int:
        return self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLOOPS_MAX)

    @property
    def allowed_num_pulses_step_size(self) -> int:
        return self._parent_io_line.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLOOPS_STEP)

    @property
    def num_pulses(self) -> int:
        """The number of pulses to generate on receipt of a trigger. If 0, pulses will be generated continuously."""
        return self._parent_io_line.read_parent_device_register(PULSE_GEN_NUM_REPEATS_COMMANDS(self._number))

    def set_num_pulses(self, num_pulses: int, coerce: bool = True) -> None:
        """Set the number of pulses to generate on receipt of a trigger. If 0 or negative, pulses will be generated
        continuously. If coerce if True, the requested number of pulses will be coerced according to min_allowed_pulses,
        max_allowed_pulses and allowed_num_pulses_step_size. Otherwise, a SpectrumInvalidParameterValue exception
        is raised if an invalid number of pulses is requested."""

        num_pulses = max(0, num_pulses)  # make negative value 0 to enable continuous pulse generation

        coerced_num_pulses = _coerce_fractional_value_to_allowed_integer(
            float(num_pulses),
            self.min_allowed_pulses,
            self.max_allowed_pulses,
            self.allowed_num_pulses_step_size
        )

        if not coerce and coerced_num_pulses != num_pulses:
            raise SpectrumInvalidParameterValue("number of pulses",
                                                num_pulses,
                                                self.min_allowed_pulses,
                                                self.max_allowed_pulses,
                                                self.allowed_num_pulses_step_size)

        self._parent_io_line.write_to_parent_device_register(PULSE_GEN_NUM_REPEATS_COMMANDS(self._number),
                                                             coerced_num_pulses)

    @property
    def min_allowed_delay_in_seconds(self) -> float:
        return self._convert_seconds_to_clock_cycles(
            self._parent_io_line.read_parent_device_register(602007)  # SPC_XIO_PULSEGEN_AVAILDELAY_MIN not in regs.py
        )

    @property
    def max_allowed_delay_in_seconds(self) -> float:
        return self._convert_seconds_to_clock_cycles(
            self._parent_io_line.read_parent_device_register(602008)  # SPC_XIO_PULSEGEN_AVAILDELAY_MAX not in regs.py
        )

    @property
    def allowed_delay_step_size_in_seconds(self) -> float:
        return self._convert_seconds_to_clock_cycles(
            self._parent_io_line.read_parent_device_register(602009)  # SPC_XIO_PULSEGEN_AVAILDELAY_STEP not in regs.py
        )

    @property
    def delay_in_seconds(self) -> float:
        """The delay between the trigger and the first pulse transmission"""
        return self._convert_clock_cycles_to_seconds(
            self._parent_io_line.read_parent_device_register(PULSE_GEN_DELAY_COMMANDS(self._number))
        )

    def set_delay_in_seconds(self, delay_in_seconds: float, coerce: bool = True) -> float:
        """Set the delay between the trigger and the first pulse transmission. If coerce=True, the requested value is
        coerced according to min_allowed_delay_in_seconds, max_allowed_delay_in_seconds and
        allowed_delay_step_size_in_seconds, and then the coerced value is returned. Otherwise, an ValueError is raised
        if the requested value is invalid."""

        requested_delay_in_clock_cycles = self._convert_seconds_to_clock_cycles(delay_in_seconds)
        clipped_delay_in_clock_cycles = _coerce_fractional_value_to_allowed_integer(
            requested_delay_in_clock_cycles,
            int(self._convert_seconds_to_clock_cycles(self.min_allowed_delay_in_seconds)),
            int(self._convert_seconds_to_clock_cycles(self.max_allowed_delay_in_seconds)),
            int(self._convert_seconds_to_clock_cycles(self.allowed_delay_step_size_in_seconds))
        )

        if not coerce and clipped_delay_in_clock_cycles != requested_delay_in_clock_cycles:
            raise SpectrumInvalidParameterValue("delay in seconds",
                                                requested_delay_in_clock_cycles,
                                                self.min_allowed_delay_in_seconds,
                                                self.max_allowed_delay_in_seconds,
                                                self.allowed_delay_step_size_in_seconds)

        self._parent_io_line.write_to_parent_device_register(PULSE_GEN_DELAY_COMMANDS(self._number),
                                                             clipped_delay_in_clock_cycles)
        return self._convert_clock_cycles_to_seconds(clipped_delay_in_clock_cycles)


def _coerce_fractional_value_to_allowed_integer(fractional_value: float, min_allowed: int, max_allowed: int,
                                                step: int) -> int:
    coerced = int(round(fractional_value / step) * step)
    return clip(coerced, min_allowed, max_allowed)


