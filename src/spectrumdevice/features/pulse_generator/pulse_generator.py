from numpy import clip

from spectrum_gmbh.py_header.regs import (
    SPCM_PULSEGEN_CONFIG_INVERT,
    SPC_PCIEXTFEATURES,
    SPC_XIO_PULSEGEN_AVAILLEN_MAX,
    SPC_XIO_PULSEGEN_AVAILLEN_MIN,
    SPC_XIO_PULSEGEN_AVAILLEN_STEP,
    SPC_XIO_PULSEGEN_AVAILLOOPS_MAX,
    SPC_XIO_PULSEGEN_AVAILLOOPS_MIN,
    SPC_XIO_PULSEGEN_AVAILLOOPS_STEP,
    SPC_XIO_PULSEGEN_CLOCK,
    SPC_XIO_PULSEGEN_ENABLE,
)
from spectrumdevice.devices.abstract_device.channel_interfaces import SpectrumIOLineInterface
from spectrumdevice.exceptions import SpectrumFeatureNotSupportedByCard, SpectrumInvalidParameterValue
from spectrumdevice.features.pulse_generator.interfaces import (
    PulseGeneratorInterface,
)
from spectrumdevice.features.pulse_generator.multiplexer import PulseGeneratorMultiplexer1, PulseGeneratorMultiplexer2
from spectrumdevice.settings import AdvancedCardFeature, SpectrumRegisterLength
from spectrumdevice.settings.card_features import decode_advanced_card_features
from spectrumdevice.settings.pulse_generator import (
    PULSE_GEN_CONFIG_COMMANDS,
    PULSE_GEN_DELAY_COMMANDS,
    PULSE_GEN_ENABLE_COMMANDS,
    PULSE_GEN_PULSE_PERIOD_COMMANDS,
    PULSE_GEN_HIGH_DURATION_COMMANDS,
    PULSE_GEN_NUM_REPEATS_COMMANDS,
    PULSE_GEN_TRIGGER_MODE_COMMANDS,
    PulseGeneratorOutputSettings,
    PulseGeneratorTriggerDetectionMode,
    PulseGeneratorTriggerMode,
    PulseGeneratorTriggerSettings,
    decode_enabled_pulse_gens,
    decode_pulse_gen_config,
)
from spectrumdevice.spectrum_wrapper import toggle_bitmap_value


class PulseGenerator(PulseGeneratorInterface):
    def __init__(self, parent: SpectrumIOLineInterface):
        self._parent_io_line = parent
        # last char of IO line name is IO line chanel number, which is used to set pulse generator number
        self._number = int(parent.name.name[-1])
        available_advanced_features = decode_advanced_card_features(
            self.read_parent_device_register(SPC_PCIEXTFEATURES)
        )
        if AdvancedCardFeature.SPCM_FEAT_EXTFW_PULSEGEN not in available_advanced_features:
            raise SpectrumFeatureNotSupportedByCard(
                call_description=self.__str__() + ".__init__()",
                message="Pulse generator firmware option not installed on device.",
            )
        self._multiplexer_1 = PulseGeneratorMultiplexer1(parent=self)
        self._multiplexer_2 = PulseGeneratorMultiplexer2(parent=self)

    def configure_output(self, settings: PulseGeneratorOutputSettings) -> None:
        self.set_period_in_seconds(settings.period_in_seconds)
        self.set_duty_cycle(settings.duty_cycle)
        self.set_num_pulses(settings.num_pulses)
        self.set_delay_in_seconds(settings.delay_in_seconds)
        self.set_output_inversion(settings.output_inversion)

    def configure_trigger(self, settings: PulseGeneratorTriggerSettings) -> None:
        self.set_trigger_mode(settings.trigger_mode)
        self.set_trigger_detection_mode(settings.trigger_detection_mode)
        self.multiplexer_1.set_trigger_source(settings.multiplexer_1_source)
        self.multiplexer_2.set_trigger_source(settings.multiplexer_2_source)
        self.multiplexer_1.set_output_inversion(settings.multiplexer_1_output_inversion)
        self.multiplexer_2.set_output_inversion(settings.multiplexer_2_output_inversion)

    @property
    def number(self) -> int:
        return self._number

    @property
    def multiplexer_1(self) -> PulseGeneratorMultiplexer1:
        return self._multiplexer_1

    @property
    def multiplexer_2(self) -> PulseGeneratorMultiplexer2:
        return self._multiplexer_2

    def read_parent_device_register(
        self, spectrum_register: int, length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO
    ) -> int:
        return self._parent_io_line.read_parent_device_register(spectrum_register, length)

    def write_to_parent_device_register(
        self,
        spectrum_register: int,
        value: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> None:
        self._parent_io_line.write_to_parent_device_register(spectrum_register, value, length)

    def _convert_clock_cycles_to_seconds(self, clock_cycles: int) -> float:
        return clock_cycles * self.clock_period_in_seconds

    def _convert_seconds_to_clock_cycles(self, seconds: float) -> float:
        return seconds * self.clock_rate_in_hz

    def _get_enabled_pulse_generator_ids(self) -> list[int]:
        return decode_enabled_pulse_gens(self.read_parent_device_register(SPC_XIO_PULSEGEN_ENABLE))

    @property
    def clock_rate_in_hz(self) -> int:
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_CLOCK)

    @property
    def clock_period_in_seconds(self) -> float:
        return 1 / self.clock_rate_in_hz

    @property
    def enabled(self) -> bool:
        return PULSE_GEN_ENABLE_COMMANDS[self._number] in self._get_enabled_pulse_generator_ids()

    def enable(self) -> None:
        current_register_value = self.read_parent_device_register(SPC_XIO_PULSEGEN_ENABLE)
        new_register_value = toggle_bitmap_value(current_register_value, PULSE_GEN_ENABLE_COMMANDS[self._number], True)
        self.write_to_parent_device_register(SPC_XIO_PULSEGEN_ENABLE, new_register_value)

    def disable(self) -> None:
        current_register_value = self.read_parent_device_register(SPC_XIO_PULSEGEN_ENABLE)
        new_register_value = toggle_bitmap_value(current_register_value, PULSE_GEN_ENABLE_COMMANDS[self._number], False)
        self.write_to_parent_device_register(SPC_XIO_PULSEGEN_ENABLE, new_register_value)

    @property
    def output_inversion(self) -> bool:
        currently_enabled_config_options = decode_pulse_gen_config(
            self.read_parent_device_register(PULSE_GEN_CONFIG_COMMANDS[self._number])
        )
        return SPCM_PULSEGEN_CONFIG_INVERT in currently_enabled_config_options

    def set_output_inversion(self, inverted: bool) -> None:
        current_register_value = self.read_parent_device_register(PULSE_GEN_CONFIG_COMMANDS[self._number])
        new_register_value = toggle_bitmap_value(current_register_value, SPCM_PULSEGEN_CONFIG_INVERT, inverted)
        self.write_to_parent_device_register(PULSE_GEN_CONFIG_COMMANDS[self._number], new_register_value)

    @property
    def trigger_detection_mode(self) -> PulseGeneratorTriggerDetectionMode:
        currently_enabled_config_options = decode_pulse_gen_config(
            self.read_parent_device_register(PULSE_GEN_CONFIG_COMMANDS[self._number])
        )
        if PulseGeneratorTriggerDetectionMode.SPCM_PULSEGEN_CONFIG_HIGH.value in currently_enabled_config_options:
            return PulseGeneratorTriggerDetectionMode.SPCM_PULSEGEN_CONFIG_HIGH
        else:
            return PulseGeneratorTriggerDetectionMode.RISING_EDGE

    def set_trigger_detection_mode(self, mode: PulseGeneratorTriggerDetectionMode) -> None:
        current_register_value = self.read_parent_device_register(PULSE_GEN_CONFIG_COMMANDS[self._number])
        high_voltage_mode_value = PulseGeneratorTriggerDetectionMode.SPCM_PULSEGEN_CONFIG_HIGH.value
        new_register_value = toggle_bitmap_value(
            current_register_value,
            high_voltage_mode_value,
            mode == PulseGeneratorTriggerDetectionMode.SPCM_PULSEGEN_CONFIG_HIGH,
        )
        self.write_to_parent_device_register(PULSE_GEN_CONFIG_COMMANDS[self._number], new_register_value)

    @property
    def trigger_mode(self) -> PulseGeneratorTriggerMode:
        return PulseGeneratorTriggerMode(
            self.read_parent_device_register(PULSE_GEN_TRIGGER_MODE_COMMANDS[self._number])
        )

    def set_trigger_mode(self, mode: PulseGeneratorTriggerMode) -> None:
        self.write_to_parent_device_register(PULSE_GEN_TRIGGER_MODE_COMMANDS[self._number], mode.value)

    @property
    def min_allowed_period_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_MIN))

    @property
    def max_allowed_period_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_MAX))

    @property
    def _allowed_period_step_size_in_clock_cycles(self) -> int:
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_STEP)

    @property
    def allowed_period_step_size_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(self._allowed_period_step_size_in_clock_cycles)

    @property
    def period_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self.read_parent_device_register(PULSE_GEN_PULSE_PERIOD_COMMANDS[self._number])
        )

    def set_period_in_seconds(self, period: float, coerce: bool = True) -> None:
        """Set the time between the start of each generated pulse in seconds. If coerce is True, the requested value
        will be coerced according to min_allowed_period_in_seconds, max_allowed_period_in_seconds and
        allowed_period_step_size_in_seconds. Otherwise, when an invalid value is requested a
        SpectrumInvalidParameterValue will be raised. The allowed values are affected by the number of active
        channels and the sample rate."""
        period_in_clock_cycles = self._convert_seconds_to_clock_cycles(period)
        coerced_period = _coerce_fractional_value_to_allowed_integer(
            period_in_clock_cycles,
            int(self._convert_seconds_to_clock_cycles(self.min_allowed_period_in_seconds)),
            int(self._convert_seconds_to_clock_cycles(self.max_allowed_period_in_seconds)),
            self._allowed_period_step_size_in_clock_cycles,
        )
        if not coerce and coerced_period != period:
            raise SpectrumInvalidParameterValue(
                "pulse generator period",
                period_in_clock_cycles,
                self.min_allowed_period_in_seconds,
                self.max_allowed_period_in_seconds,
                self.allowed_period_step_size_in_seconds,
            )

        self.write_to_parent_device_register(PULSE_GEN_PULSE_PERIOD_COMMANDS[self._number], int(coerced_period))

    @property
    def min_allowed_high_voltage_duration_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_MIN))

    @property
    def max_allowed_high_voltage_duration_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_MAX))

    @property
    def _allowed_high_voltage_duration_step_size_in_clock_cycles(self) -> int:
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_STEP)

    @property
    def allowed_high_voltage_duration_step_size_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(self._allowed_period_step_size_in_clock_cycles)

    @property
    def duration_of_high_voltage_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self.read_parent_device_register(PULSE_GEN_HIGH_DURATION_COMMANDS[self._number])
        )

    @property
    def duration_of_low_voltage_in_seconds(self) -> float:
        return self.period_in_seconds - self.duration_of_high_voltage_in_seconds

    @property
    def duty_cycle(self) -> float:
        return self.duration_of_high_voltage_in_seconds / self.period_in_seconds

    def set_duty_cycle(self, duty_cycle: float, coerce: bool = True) -> float:
        """Set the duty cycle. If coerce is True, the requested value will be coerced to be within allowed range and
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
            self._allowed_high_voltage_duration_step_size_in_clock_cycles,
        )
        if not coerce and clipped_duration != requested_high_v_duration_in_clock_cycles:
            raise SpectrumInvalidParameterValue(
                "high-voltage duration",
                duty_cycle,
                self.min_allowed_high_voltage_duration_in_seconds,
                self.max_allowed_high_voltage_duration_in_seconds,
                self._allowed_high_voltage_duration_step_size_in_clock_cycles,
            )
        self.write_to_parent_device_register(PULSE_GEN_HIGH_DURATION_COMMANDS[self._number], clipped_duration)
        return self._convert_clock_cycles_to_seconds(clipped_duration) / self.period_in_seconds

    @property
    def min_allowed_pulses(self) -> int:
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLOOPS_MIN)

    @property
    def max_allowed_pulses(self) -> int:
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLOOPS_MAX)

    @property
    def allowed_num_pulses_step_size(self) -> int:
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLOOPS_STEP)

    @property
    def num_pulses(self) -> int:
        """The number of pulses to generate on receipt of a trigger. If 0, pulses will be generated continuously."""
        return self.read_parent_device_register(PULSE_GEN_NUM_REPEATS_COMMANDS[self._number])

    def set_num_pulses(self, num_pulses: int, coerce: bool = True) -> None:
        """Set the number of pulses to generate on receipt of a trigger. If 0 or negative, pulses will be generated
        continuously. If coerce if True, the requested number of pulses will be coerced according to min_allowed_pulses,
        max_allowed_pulses and allowed_num_pulses_step_size. Otherwise, a SpectrumInvalidParameterValue exception
        is raised if an invalid number of pulses is requested."""

        num_pulses = max(0, num_pulses)  # make negative value 0 to enable continuous pulse generation

        coerced_num_pulses = _coerce_fractional_value_to_allowed_integer(
            float(num_pulses), self.min_allowed_pulses, self.max_allowed_pulses, self.allowed_num_pulses_step_size
        )

        if not coerce and coerced_num_pulses != num_pulses:
            raise SpectrumInvalidParameterValue(
                "number of pulses",
                num_pulses,
                self.min_allowed_pulses,
                self.max_allowed_pulses,
                self.allowed_num_pulses_step_size,
            )

        self.write_to_parent_device_register(PULSE_GEN_NUM_REPEATS_COMMANDS[self._number], coerced_num_pulses)

    @property
    def min_allowed_delay_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self.read_parent_device_register(602007)  # SPC_XIO_PULSEGEN_AVAILDELAY_MIN not in regs.py
        )

    @property
    def max_allowed_delay_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self.read_parent_device_register(602008)  # SPC_XIO_PULSEGEN_AVAILDELAY_MAX not in regs.py
        )

    @property
    def allowed_delay_step_size_in_seconds(self) -> float:
        return self._convert_clock_cycles_to_seconds(
            self.read_parent_device_register(602009)  # SPC_XIO_PULSEGEN_AVAILDELAY_STEP not in regs.py
        )

    @property
    def delay_in_seconds(self) -> float:
        """The delay between the trigger and the first pulse transmission"""
        return self._convert_clock_cycles_to_seconds(
            self.read_parent_device_register(PULSE_GEN_DELAY_COMMANDS[self._number])
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
            int(self._convert_seconds_to_clock_cycles(self.allowed_delay_step_size_in_seconds)),
        )

        if not coerce and clipped_delay_in_clock_cycles != requested_delay_in_clock_cycles:
            raise SpectrumInvalidParameterValue(
                "delay in seconds",
                requested_delay_in_clock_cycles,
                self.min_allowed_delay_in_seconds,
                self.max_allowed_delay_in_seconds,
                self.allowed_delay_step_size_in_seconds,
            )

        self.write_to_parent_device_register(PULSE_GEN_DELAY_COMMANDS[self._number], clipped_delay_in_clock_cycles)
        return self._convert_clock_cycles_to_seconds(clipped_delay_in_clock_cycles)

    def __str__(self) -> str:
        return f"Pulse generator {self._number} of {self._parent_io_line}."


def _coerce_fractional_value_to_allowed_integer(
    fractional_value: float, min_allowed: int, max_allowed: int, step: int
) -> int:
    coerced = int(round(fractional_value / step) * step)
    return int(clip(coerced, min_allowed, max_allowed))
