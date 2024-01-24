import numpy as np
from numpy import clip, int16, iinfo

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
    SPC_XIO_PULSEGEN_COMMAND,
    SPCM_PULSEGEN_CMD_FORCE,
    SPC_M2CMD,
    M2CMD_CARD_WRITESETUP,
    SPC_XIO_PULSEGEN_AVAILHIGH_STEP,
    SPC_XIO_PULSEGEN_AVAILHIGH_MAX,
    SPC_XIO_PULSEGEN_AVAILHIGH_MIN,
)
from spectrumdevice.devices.abstract_device.channel_interfaces import SpectrumIOLineInterface
from spectrumdevice.exceptions import (
    SpectrumFeatureNotSupportedByCard,
    SpectrumInvalidParameterValue,
    SpectrumIOError,
)
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
    PulseGeneratorMultiplexer2TriggerSource,
)
from spectrumdevice.spectrum_wrapper import toggle_bitmap_value


class PulseGenerator(PulseGeneratorInterface):
    """Class for controlling pulse generators associated with IO lines (requires firmware option be enabled)."""

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

    def configure_output(
        self, settings: PulseGeneratorOutputSettings, coerce: bool = True
    ) -> PulseGeneratorOutputSettings:
        """Configure all pulse generator output settings at once. By default, all values are coerced to the
        nearest values allowed by the hardware, and the coerced values are returned."""
        self.set_output_inversion(settings.output_inversion)
        coerced_settings = PulseGeneratorOutputSettings(
            period_in_seconds=self.set_period_in_seconds(settings.period_in_seconds, coerce=coerce),
            duty_cycle=self.set_duty_cycle(settings.duty_cycle, coerce=coerce),
            num_pulses=self.set_num_pulses(settings.num_pulses, coerce=coerce),
            delay_in_seconds=self.set_delay_in_seconds(settings.delay_in_seconds, coerce=coerce),
            output_inversion=settings.output_inversion,
        )
        self.write_to_parent_device_register(SPC_M2CMD, M2CMD_CARD_WRITESETUP)
        return coerced_settings

    def configure_trigger(self, settings: PulseGeneratorTriggerSettings) -> None:
        """Configure all pulse generator trigger settings at once."""
        self.set_trigger_mode(settings.trigger_mode)
        self.set_trigger_detection_mode(settings.trigger_detection_mode)
        self.multiplexer_1.set_trigger_source(settings.multiplexer_1_source)
        self.multiplexer_2.set_trigger_source(settings.multiplexer_2_source)
        self.multiplexer_1.set_output_inversion(settings.multiplexer_1_output_inversion)
        self.multiplexer_2.set_output_inversion(settings.multiplexer_2_output_inversion)
        self.write_to_parent_device_register(SPC_M2CMD, M2CMD_CARD_WRITESETUP)

    def force_trigger(self) -> None:
        """Generates a pulse when the pulse generator trigger source (mux 2) is set to 'software'."""
        if (
            self._multiplexer_2.trigger_source
            != PulseGeneratorMultiplexer2TriggerSource.SPCM_PULSEGEN_MUX2_SRC_SOFTWARE
        ):
            raise SpectrumIOError("Force trigger can only be used if trigger source (mux 2) is set to 'software'")
        self.write_to_parent_device_register(SPC_XIO_PULSEGEN_COMMAND, SPCM_PULSEGEN_CMD_FORCE)

    @property
    def number(self) -> int:
        """The index of the pulse generator. Corresponds to the index of the IO line to which it belongs."""
        return self._number

    @property
    def multiplexer_1(self) -> PulseGeneratorMultiplexer1:
        """Change the trigger source of this multiplexer to control when it is possible to trigger the pulse generator."""
        return self._multiplexer_1

    @property
    def multiplexer_2(self) -> PulseGeneratorMultiplexer2:
        """Change the trigger source of this multiplexer to control how the pulse generator is triggered."""
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
        # round to nearest milli-cycle to avoid floating point precision problems
        return round(seconds * self.clock_rate_in_hz * 1e3) / 1e3

    def _get_enabled_pulse_generator_ids(self) -> list[int]:
        return decode_enabled_pulse_gens(self.read_parent_device_register(SPC_XIO_PULSEGEN_ENABLE))

    @property
    def clock_rate_in_hz(self) -> int:
        """The current pulse generator clock rate. Affected by the sample rate of the parent card, and the number of
        channels enabled. Effects the precision with which pulse timings can be set, and their min and max values."""
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_CLOCK)

    @property
    def clock_period_in_seconds(self) -> float:
        """The reciprocal of the clock rate, in seconds."""
        return 1 / self.clock_rate_in_hz

    @property
    def enabled(self) -> bool:
        """True if the pulse generator is currently enabled."""
        return PULSE_GEN_ENABLE_COMMANDS[self._number] in self._get_enabled_pulse_generator_ids()

    def enable(self) -> None:
        """Enable the pulse generator. Note that the mode of the parent IO Line must also be set to
        IOLineMOdO.SPCM_XMODE_PULSEGEN."""
        current_register_value = self.read_parent_device_register(SPC_XIO_PULSEGEN_ENABLE)
        new_register_value = toggle_bitmap_value(current_register_value, PULSE_GEN_ENABLE_COMMANDS[self._number], True)
        self.write_to_parent_device_register(SPC_XIO_PULSEGEN_ENABLE, new_register_value)

    def disable(self) -> None:
        """Disable the pulse generator."""
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
        """How the pulse generator trigger circuit responds to a trigger signal, .e.g rising edge..."""
        currently_enabled_config_options = decode_pulse_gen_config(
            self.read_parent_device_register(PULSE_GEN_CONFIG_COMMANDS[self._number])
        )
        if PulseGeneratorTriggerDetectionMode.SPCM_PULSEGEN_CONFIG_HIGH.value in currently_enabled_config_options:
            return PulseGeneratorTriggerDetectionMode.SPCM_PULSEGEN_CONFIG_HIGH
        else:
            return PulseGeneratorTriggerDetectionMode.RISING_EDGE

    def set_trigger_detection_mode(self, mode: PulseGeneratorTriggerDetectionMode) -> None:
        """e.g. rising edge, high-voltage..."""
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
        """Gated, triggered or single-shot. See PulseGeneratorTriggerMode for more information."""
        return PulseGeneratorTriggerMode(
            self.read_parent_device_register(PULSE_GEN_TRIGGER_MODE_COMMANDS[self._number])
        )

    def set_trigger_mode(self, mode: PulseGeneratorTriggerMode) -> None:
        """Gated, triggered or single-shot. See PulseGeneratorTriggerMode for more information."""
        self.write_to_parent_device_register(PULSE_GEN_TRIGGER_MODE_COMMANDS[self._number], mode.value)

    @property
    def min_allowed_period_in_seconds(self) -> float:
        """Minimum allowed pulse period in seconds, given the current clock rate."""
        reg_val = self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_MIN)
        reg_val = 0 if reg_val < 0 else reg_val
        return self._convert_clock_cycles_to_seconds(reg_val)

    @property
    def max_allowed_period_in_seconds(self) -> float:
        """Maximum allowed pulse period in seconds, given the current clock rate."""
        reg_val = self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_MAX)
        reg_val = iinfo(int16).max if reg_val < 0 else reg_val
        return self._convert_clock_cycles_to_seconds(reg_val)

    @property
    def _allowed_period_step_size_in_clock_cycles(self) -> int:
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLEN_STEP)

    @property
    def allowed_period_step_size_in_seconds(self) -> float:
        """Resolution with which the pulse period can be set, given the current clock rate."""
        return self._convert_clock_cycles_to_seconds(self._allowed_period_step_size_in_clock_cycles)

    @property
    def period_in_seconds(self) -> float:
        """The pulse length in seconds, including both the high-voltage and low-voltage sections."""
        return self._convert_clock_cycles_to_seconds(
            self.read_parent_device_register(PULSE_GEN_PULSE_PERIOD_COMMANDS[self._number])
        )

    def set_period_in_seconds(self, period: float, coerce: bool = False) -> float:
        """Set the time between the start of each generated pulse in seconds. If coerce is True, the requested value
        will be coerced according to min_allowed_period_in_seconds, max_allowed_period_in_seconds and
        allowed_period_step_size_in_seconds and the coerced value is returned. Otherwise, when an invalid value is
        requested a SpectrumInvalidParameterValue will be raised. The allowed values are affected by the number of
        active channels and the sample rate."""
        period_in_clock_cycles = self._convert_seconds_to_clock_cycles(period)
        coerced_period = _coerce_fractional_value_to_allowed_integer(
            period_in_clock_cycles,
            int(self._convert_seconds_to_clock_cycles(self.min_allowed_period_in_seconds)),
            int(self._convert_seconds_to_clock_cycles(self.max_allowed_period_in_seconds)),
            self._allowed_period_step_size_in_clock_cycles,
        )
        if not coerce and coerced_period != period_in_clock_cycles:
            raise SpectrumInvalidParameterValue(
                "pulse generator period",
                period,
                self.min_allowed_period_in_seconds,
                self.max_allowed_period_in_seconds,
                self.allowed_period_step_size_in_seconds,
            )

        self.write_to_parent_device_register(PULSE_GEN_PULSE_PERIOD_COMMANDS[self._number], int(coerced_period))
        return self._convert_clock_cycles_to_seconds(coerced_period)

    @property
    def min_allowed_high_voltage_duration_in_seconds(self) -> float:
        """Minimum allowed duration of the high-voltage part of the pulse in seconds, given the current clock rate."""
        reg_val = self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILHIGH_MIN)
        reg_val = 0 if reg_val < 0 else reg_val
        return self._convert_clock_cycles_to_seconds(reg_val)

    @property
    def max_allowed_high_voltage_duration_in_seconds(self) -> float:
        """Maximum allowed duration of the high-voltage part of the pulse in seconds, given the current clock rate."""
        reg_val = self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILHIGH_MAX)
        reg_val = iinfo(int16).max if reg_val < 0 else reg_val
        return self._convert_clock_cycles_to_seconds(reg_val)

    @property
    def _allowed_high_voltage_duration_step_size_in_clock_cycles(self) -> int:
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILHIGH_STEP)

    @property
    def allowed_high_voltage_duration_step_size_in_seconds(self) -> float:
        """Resolution with which the high-voltage duration can be set, in seconds, given the current clock rate."""
        return self._convert_clock_cycles_to_seconds(self._allowed_high_voltage_duration_step_size_in_clock_cycles)

    @property
    def duration_of_high_voltage_in_seconds(self) -> float:
        """The length of the high-voltage part of a pulse, in seconds. Equal to the pulse duration * duty cycle."""
        return self._convert_clock_cycles_to_seconds(
            self.read_parent_device_register(PULSE_GEN_HIGH_DURATION_COMMANDS[self._number])
        )

    @property
    def duration_of_low_voltage_in_seconds(self) -> float:
        """The length of the low-voltage part of a pulse, in seconds. Equal to the pulse duration * (1 - duty cycle)."""
        return self.period_in_seconds - self.duration_of_high_voltage_in_seconds

    @property
    def duty_cycle(self) -> float:
        """The ratio between the high-voltage and low-voltage parts of the pulse."""
        return self.duration_of_high_voltage_in_seconds / self.period_in_seconds

    def set_duty_cycle(self, duty_cycle: float, coerce: bool = False) -> float:
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
                self.period_in_seconds * duty_cycle,
                self.min_allowed_high_voltage_duration_in_seconds,
                self.max_allowed_high_voltage_duration_in_seconds,
                self.allowed_high_voltage_duration_step_size_in_seconds,
            )
        self.write_to_parent_device_register(PULSE_GEN_HIGH_DURATION_COMMANDS[self._number], clipped_duration)
        return self._convert_clock_cycles_to_seconds(clipped_duration) / self.period_in_seconds

    @property
    def min_allowed_pulses(self) -> int:
        """Minimum allowed number of pulses to transmit."""
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLOOPS_MIN)

    @property
    def max_allowed_pulses(self) -> int:
        """Maximum allowed number of pulses to transmit."""
        reg_val = self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLOOPS_MAX)
        # my card has this register set to -2, which I assume means no limit (can't work it out from the docs)
        return reg_val if reg_val > 0 else iinfo(int16).max

    @property
    def allowed_num_pulses_step_size(self) -> int:
        """Resolution with which the number of pulses to transmit can be set."""
        return self.read_parent_device_register(SPC_XIO_PULSEGEN_AVAILLOOPS_STEP)

    @property
    def num_pulses(self) -> int:
        """The number of pulses to generate on receipt of a trigger. If 0, pulses will be generated continuously."""
        return self.read_parent_device_register(PULSE_GEN_NUM_REPEATS_COMMANDS[self._number])

    def set_num_pulses(self, num_pulses: int, coerce: bool = False) -> int:
        """Set the number of pulses to generate on receipt of a trigger. If 0 or negative, pulses will be generated
        continuously. If coerce if True, the requested number of pulses will be coerced according to min_allowed_pulses,
        max_allowed_pulses and allowed_num_pulses_step_size and the coerced value is returned. Otherwise, a
        SpectrumInvalidParameterValue exception is raised if an invalid number of pulses is requested."""

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
        return coerced_num_pulses

    @property
    def min_allowed_delay_in_seconds(self) -> float:
        """Minimum allowed delay between the trigger event and pulse generation, in seconds, given the current clock
        rate."""
        reg_value = self.read_parent_device_register(602007)  # SPC_XIO_PULSEGEN_AVAILDELAY_MIN not in regs.py
        reg_value = 0 if reg_value == -1 else reg_value
        return self._convert_clock_cycles_to_seconds(reg_value)

    @property
    def max_allowed_delay_in_seconds(self) -> float:
        """Maximum allowed delay between the trigger event and pulse generation, in seconds, given the current clock
        rate."""
        reg_value = self.read_parent_device_register(602008)  # SPC_XIO_PULSEGEN_AVAILDELAY_MAX not in regs.py
        reg_value = iinfo(int16).max if reg_value == -1 else reg_value
        return self._convert_clock_cycles_to_seconds(reg_value)

    @property
    def allowed_delay_step_size_in_seconds(self) -> float:
        """resolution with which the delay between the trigger event and pulse generation can be set, in seconds, given
        the current clock rate."""
        return self._convert_clock_cycles_to_seconds(
            self.read_parent_device_register(602009)  # SPC_XIO_PULSEGEN_AVAILDELAY_STEP not in regs.py
        )

    @property
    def delay_in_seconds(self) -> float:
        """The delay between the trigger and the first pulse transmission"""
        return self._convert_clock_cycles_to_seconds(
            self.read_parent_device_register(PULSE_GEN_DELAY_COMMANDS[self._number])
        )

    def set_delay_in_seconds(self, delay_in_seconds: float, coerce: bool = False) -> float:
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
    if min_allowed == -1:
        min_allowed = 0
    if max_allowed == -1:
        max_allowed = np.iinfo(int16).max
    return int(clip(coerced, min_allowed, max_allowed))
