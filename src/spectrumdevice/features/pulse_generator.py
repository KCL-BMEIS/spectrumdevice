from numpy import clip

from spectrum_gmbh.py_header.regs import SPC_XIO_PULSEGEN_AVAILLEN_MAX, SPC_XIO_PULSEGEN_AVAILLEN_MIN, \
    SPC_XIO_PULSEGEN_AVAILLEN_STEP, SPC_XIO_PULSEGEN_AVAILLOOPS_MAX, SPC_XIO_PULSEGEN_AVAILLOOPS_MIN, \
    SPC_XIO_PULSEGEN_AVAILLOOPS_STEP, SPC_XIO_PULSEGEN_CLOCK, SPC_XIO_PULSEGEN_ENABLE
from spectrumdevice.devices.abstract_device.interfaces import SpectrumIOLineInterface
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

    def set_period_in_seconds(self, period: float) -> None:

        if not (self.min_allowed_period_in_seconds <= period <= self.max_allowed_period_in_seconds):
            raise ValueError(f"Pulse period must be between {self.min_allowed_period_in_seconds} and "
                             f"{self.max_allowed_period_in_seconds} seconds long, inclusive. Ths range is "
                             f"affected by the number of active channels and the sampling rate.")

        period_in_clock_cycles = self._convert_seconds_to_clock_cycles(period)
        period_in_allowed_steps = period_in_clock_cycles / self._allowed_period_step_size_in_clock_cycles
        if not period_in_allowed_steps.is_integer():
            raise ValueError(f"Pulse period must a multiple of {self.allowed_period_step_size_in_seconds} "
                             f"seconds.")

        self._parent_io_line.write_to_parent_device_register(
            PULSE_GEN_PULSE_PERIOD_COMMANDS(int(period_in_clock_cycles))
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

    def set_duty_cycle(self, duty_cycle: float) -> float:
        """ Set the duty cycle. Value will be coerced to be within allowed range and use allowed step size.
        The allowed values are affected by the number of active channels and the sample rate.
        The coerced value is returned."""
        requested_high_v_duration_in_clock_cycles = self._convert_seconds_to_clock_cycles(
            self.period_in_seconds * duty_cycle
        )
        step_size = self._allowed_high_voltage_duration_step_size_in_clock_cycles
        coerced_duration = round(requested_high_v_duration_in_clock_cycles / step_size) * step_size
        clipped_duration = clip(
            coerced_duration,
            int(self._convert_seconds_to_clock_cycles(self.min_allowed_high_voltage_duration_in_seconds)),
            int(self._convert_seconds_to_clock_cycles(self.max_allowed_high_voltage_duration_in_seconds))
        )
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

    def set_num_pulses(self, num_pulses: int) -> None:
        #todo: add step size check (raise ValueError if wrong step size)
        """Set the number of pulses to generate on receipt of a trigger. If 0, pulses will be generated continuously."""
        if num_pulses <= 0:
            raise ValueError("Number of pulses cannot be negative")
        if num_pulses != 0 and not (self.min_allowed_pulses <= num_pulses <= self.max_allowed_pulses):
            raise ValueError(f"Number of pulses must be between {self.min_allowed_pulses} and "
                             f"{self.max_allowed_pulses} (inclusive), or 0 for continuous pulse generation.")
        self._parent_io_line.write_to_parent_device_register(PULSE_GEN_NUM_REPEATS_COMMANDS(self._number), num_pulses)

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

    def set_delay_in_seconds(self, delay_in_seconds: float) -> None:
        """Set the delay between the trigger and the first pulse transmission"""
        #todo: add step size check (coerce if wrong step size)
        #todo: add range limits check (coerce if wrong)
        self._convert_seconds_to_clock_cycles(delay_in_seconds)




