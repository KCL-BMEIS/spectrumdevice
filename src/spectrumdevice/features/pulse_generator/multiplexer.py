from abc import ABC

from spectrumdevice.features.pulse_generator.interfaces import (
    MultiplexerTriggerSourceTypeVar,
    PulseGeneratorInterface,
    PulseGeneratorMultiplexerInterface,
)
from spectrumdevice.settings import SpectrumRegisterLength
from spectrumdevice.settings.pulse_generator import (
    PULSE_GEN_CONFIG_COMMANDS,
    PULSE_GEN_MUX1_COMMANDS,
    PULSE_GEN_MUX2_COMMANDS,
    PULSE_GEN_MUX_INVERSION_COMMANDS,
    PulseGeneratorMultiplexer1TriggerSource,
    PulseGeneratorMultiplexer2TriggerSource,
    decode_pulse_gen_config,
)
from spectrumdevice.spectrum_wrapper import toggle_bitmap_value


class PulseGeneratorMultiplexer(PulseGeneratorMultiplexerInterface[MultiplexerTriggerSourceTypeVar], ABC):
    def __init__(self, parent: PulseGeneratorInterface) -> None:
        self._parent_pulse_gen = parent

    def read_parent_device_register(
        self, spectrum_register: int, length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO
    ) -> int:
        return self._parent_pulse_gen.read_parent_device_register(spectrum_register, length)

    def write_to_parent_device_register(
        self,
        spectrum_register: int,
        value: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> None:
        self._parent_pulse_gen.write_to_parent_device_register(spectrum_register, value, length)

    @property
    def output_inversion(self) -> bool:
        currently_enabled_config_options = decode_pulse_gen_config(
            self.read_parent_device_register(PULSE_GEN_CONFIG_COMMANDS[self._parent_pulse_gen.number])
        )
        return PULSE_GEN_MUX_INVERSION_COMMANDS[self.number] in currently_enabled_config_options

    def set_output_inversion(self, inverted: bool) -> None:
        current_register_value = self.read_parent_device_register(
            PULSE_GEN_CONFIG_COMMANDS[self._parent_pulse_gen.number]
        )
        new_register_value = toggle_bitmap_value(
            current_register_value, PULSE_GEN_MUX_INVERSION_COMMANDS[self.number], inverted
        )
        self.write_to_parent_device_register(
            PULSE_GEN_CONFIG_COMMANDS[self._parent_pulse_gen.number], new_register_value
        )


class PulseGeneratorMultiplexer1(PulseGeneratorMultiplexer[PulseGeneratorMultiplexer1TriggerSource]):
    @property
    def number(self) -> int:
        return 0  # use zero-indexed value for use getting command from PULSE_GEN_MUX1_COMMANDS tuple

    @property
    def trigger_source(self) -> PulseGeneratorMultiplexer1TriggerSource:
        return PulseGeneratorMultiplexer1TriggerSource(
            self.read_parent_device_register(PULSE_GEN_MUX1_COMMANDS[self._parent_pulse_gen.number])
        )

    def set_trigger_source(self, trigger_source: PulseGeneratorMultiplexer1TriggerSource) -> None:
        self.write_to_parent_device_register(
            PULSE_GEN_MUX1_COMMANDS[self._parent_pulse_gen.number], trigger_source.value
        )


class PulseGeneratorMultiplexer2(PulseGeneratorMultiplexer[PulseGeneratorMultiplexer2TriggerSource]):
    @property
    def number(self) -> int:
        return 1  # use zero-indexed value for use getting command from PULSE_GEN_MUX1_COMMANDS tuple

    @property
    def trigger_source(self) -> PulseGeneratorMultiplexer2TriggerSource:
        return PulseGeneratorMultiplexer2TriggerSource(
            self.read_parent_device_register(PULSE_GEN_MUX2_COMMANDS[self._parent_pulse_gen.number])
        )

    def set_trigger_source(self, trigger_source: PulseGeneratorMultiplexer2TriggerSource) -> None:
        self.write_to_parent_device_register(
            PULSE_GEN_MUX2_COMMANDS[self._parent_pulse_gen.number], trigger_source.value
        )
