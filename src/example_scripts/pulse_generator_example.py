from spectrumdevice.devices.awg.awg_card import SpectrumAWGCard
from spectrumdevice.devices.mocks import MockSpectrumAWGCard
from spectrumdevice.settings import ModelNumber, IOLineMode, AdvancedCardFeature
from spectrumdevice.settings.pulse_generator import (
    PulseGeneratorTriggerSettings,
    PulseGeneratorTriggerMode,
    PulseGeneratorTriggerDetectionMode,
    PulseGeneratorMultiplexer1TriggerSource,
    PulseGeneratorMultiplexer2TriggerSource,
    PulseGeneratorOutputSettings,
)


def pulse_generator_example(mock_mode: bool) -> None:

    # Create connection to a mock or real card. Here we are using an AWG but could be a digitiser
    if not mock_mode:
        card = SpectrumAWGCard(device_number=0)
    else:
        card = MockSpectrumAWGCard(
            device_number=0,
            model=ModelNumber.TYP_M2P6560_X4,
            num_modules=1,
            num_channels_per_module=1,
            # make sure the mock card has the pulse generator feature unlocked!
            advanced_card_features=[AdvancedCardFeature.SPCM_FEAT_EXTFW_PULSEGEN],
        )

    # Set the card's sample rate. This affects the precision with which pulse timings can be chosen, and the min and max
    # allowed pulse periods
    card.set_sample_rate_in_hz(8000000)
    # Enable a single channel of the card. Although not used in this example, the number of enabled channels affects
    # the precision with which pulse timings can be chosen and the min and max allowed pulse periods
    card.set_enabled_analog_channels([0])

    # Each of the card's four multipurpose IO lines (X0, X1, X2 and X3) has a pulse generator
    # Choose the one you would like to use and set it to pulse gen mode. Here we are using X1 (index 1)
    io_line_index = 1
    card.io_lines[io_line_index].set_mode(IOLineMode.SPCM_XMODE_PULSEGEN)
    # Then get its pulse generator
    pulse_gen = card.io_lines[io_line_index].pulse_generator

    # Configure the trigger behavior.
    # Here we are configuring a software trigger by setting multiplexer 2 source to SPCM_PULSEGEN_MUX2_SRC_SOFTWARE
    # Setting multiplexer 1 source to SPCM_PULSEGEN_MUX1_SRC_UNUSED means that the software trigger will work weather or
    # not the card is armed or started
    # The trigger mode of SINGLESHOT means the pulse generator will wait for a single trigger, and then will output
    # a predefined number of pulses before stopping (and not rearming)
    pg_trigger_settings = PulseGeneratorTriggerSettings(
        trigger_mode=PulseGeneratorTriggerMode.SPCM_PULSEGEN_MODE_SINGLESHOT,
        trigger_detection_mode=PulseGeneratorTriggerDetectionMode.RISING_EDGE,
        multiplexer_1_source=PulseGeneratorMultiplexer1TriggerSource.SPCM_PULSEGEN_MUX1_SRC_UNUSED,
        multiplexer_1_output_inversion=False,
        multiplexer_2_source=PulseGeneratorMultiplexer2TriggerSource.SPCM_PULSEGEN_MUX2_SRC_SOFTWARE,
        multiplexer_2_output_inversion=False,
    )
    pulse_gen.configure_trigger(pg_trigger_settings)

    # Configure the pulse output
    # The pulse generator will output num_pulses pulses on receipt of a trigger before stopping. Set to 0 for
    # continuous output
    # The period is the length of the whole pulse (high-voltage length + 0V length)
    # The duty cycle is the high-voltage length divided by the period
    pulse_output_settings = PulseGeneratorOutputSettings(
        period_in_seconds=1e-3, duty_cycle=0.01, num_pulses=1000, delay_in_seconds=0.0, output_inversion=False
    )
    pulse_gen.configure_output(pulse_output_settings, coerce=False)

    # Print pulse timings. They may have been coerced to allowed values
    print(f"Pulse period: {pulse_gen.period_in_seconds * 1e3} ms")
    print(f"Duty cycle: {pulse_gen.duty_cycle}")

    # Enable the pulse generator
    pulse_gen.enable()

    # Generate a software trigger to start outputting pulses
    pulse_gen.force_trigger()

    card.stop()
    card.disconnect()


if __name__ == "__main__":
    pulse_generator_example(mock_mode=False)
