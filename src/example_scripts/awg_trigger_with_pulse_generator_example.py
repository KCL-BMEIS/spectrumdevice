from time import sleep

from numpy import int16

from spectrumdevice.devices.awg.synthesis import make_full_scale_rect_waveform
from spectrumdevice.devices.mocks import MockSpectrumAWGCard
from spectrumdevice.settings import (
    TriggerSettings,
    TriggerSource,
    ExternalTriggerMode,
    IOLineMode,
    ModelNumber,
    AdvancedCardFeature,
    GenerationSettings,
    OutputChannelFilter,
)
from spectrumdevice.settings.channel import OutputChannelStopLevelMode
from spectrumdevice.settings.device_modes import GenerationMode
from spectrumdevice.settings.pulse_generator import (
    PulseGeneratorOutputSettings,
    PulseGeneratorTriggerSettings,
    PulseGeneratorTriggerMode,
    PulseGeneratorTriggerDetectionMode,
    PulseGeneratorMultiplexer1TriggerSource,
    PulseGeneratorMultiplexer2TriggerSource,
)


SAMPLE_RATE_IN_HZ = 40000000
NUM_GENERATIONS = 4


if __name__ == "__main__":

    # AWG CARD SETUP ---------------------------------------------------------------------------------------------------

    # Connect to a real AWG card with the optional pulse generator firmware option unlocked
    # card = SpectrumAWGCard(device_number=0)

    # Or a mock AWG card
    card = MockSpectrumAWGCard(
        device_number=0,
        model=ModelNumber.TYP_M2P6560_X4,
        num_modules=1,
        num_channels_per_module=1,
        # make sure the mock card has the pulse generator feature unlocked!
        advanced_card_features=[AdvancedCardFeature.SPCM_FEAT_EXTFW_PULSEGEN],
    )

    # Set up the AWG trigger settings using the X1 multipurpose IO Line as a trigger source
    card_trigger_settings = TriggerSettings(
        # ext1 trigger source is the X1 I/O Line (X0 cannot be used as a trigger source because it is output-only)
        trigger_sources=[TriggerSource.SPC_TMASK_EXT1],
        external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
    )
    card.configure_trigger(card_trigger_settings)

    # Create an AWG waveform to generate
    t, analog_wfm = make_full_scale_rect_waveform(
        sample_rate_in_hz=SAMPLE_RATE_IN_HZ, duration_in_seconds=0.25e-3, dtype=int16
    )

    # Configure signal generation. SINGLERESTART mode means that, on receipt of a trigger, the AWG will output its
    # waveform and then wait for another trigger. The card will stop once num_loops waveforms have been generated.
    generation_settings = GenerationSettings(
        generation_mode=GenerationMode.SPC_REP_STD_SINGLERESTART,
        waveform=analog_wfm,
        sample_rate_in_hz=SAMPLE_RATE_IN_HZ,
        num_loops=NUM_GENERATIONS,
        enabled_channels=[0],
        signal_amplitudes_in_mv=[1000],
        dc_offsets_in_mv=[0],
        output_filters=[OutputChannelFilter.LOW_PASS_70_MHZ],
        stop_level_modes=[OutputChannelStopLevelMode.SPCM_STOPLVL_ZERO],
    )
    card.configure_generation(generation_settings)

    # Each of the card's four multipurpose IO lines (X0, X1, X2 and X3) has a pulse generator
    # Choose the one you would like to use and set it to pulse gen mode. Here we are using X1 (index 1) because
    # X0 is output-only and can therefore not be selected as a trigger source for the AWG.
    io_line_index = 1
    card.io_lines[io_line_index].set_mode(IOLineMode.SPCM_XMODE_PULSEGEN)

    # PULSE GENERATOR SETUP --------------------------------------------------------------------------------------------

    # Get the IO Line's pulse generator
    pulse_gen = card.io_lines[io_line_index].pulse_generator

    # Configure the pulse generator's trigger settings
    # Here we are configuring a software trigger by setting multiplexer 2 source to SPCM_PULSEGEN_MUX2_SRC_SOFTWARE
    # Setting multiplexer 1 source to SPCM_PULSEGEN_MUX1_SRC_UNUSED means that the software trigger will work weather or
    # not the card is armed or started
    # The trigger mode of SINGLESHOT means the pulse generator will wait for a single trigger, and then will output
    # a predefined number of pulses before stopping (and not rearming)
    pulse_trigger_settings = PulseGeneratorTriggerSettings(
        trigger_mode=PulseGeneratorTriggerMode.SPCM_PULSEGEN_MODE_SINGLESHOT,
        trigger_detection_mode=PulseGeneratorTriggerDetectionMode.RISING_EDGE,
        multiplexer_1_source=PulseGeneratorMultiplexer1TriggerSource.SPCM_PULSEGEN_MUX1_SRC_UNUSED,
        multiplexer_1_output_inversion=False,
        multiplexer_2_source=PulseGeneratorMultiplexer2TriggerSource.SPCM_PULSEGEN_MUX2_SRC_SOFTWARE,
        multiplexer_2_output_inversion=False,
    )
    pulse_gen.configure_trigger(pulse_trigger_settings)

    # Configure the pulse generator output
    # The pulse generator will output num_pulses pulses on receipt of a trigger before stopping. Set to 0 for
    # continuous output
    # The period is the length of the whole pulse (high-voltage length + 0V length)
    # The duty cycle is the high-voltage length divided by the period
    pulse_output_settings = PulseGeneratorOutputSettings(
        period_in_seconds=1e-3, duty_cycle=0.5, num_pulses=NUM_GENERATIONS, delay_in_seconds=0.0, output_inversion=False
    )
    pulse_gen.configure_output(pulse_output_settings)

    # Enable the pulse generator
    pulse_gen.enable()

    # Start the AWG so it is waiting for a trigger
    card.start()

    # Force a software trigger on the pulse generator, causing pulse to be generated on X1, triggering the AWG
    pulse_gen.force_trigger()
    # Wait for the pulse sequence to complete
    sleep(1)

    # Note that there is a delay between a trigger being received and the AWG generating a signal.
    # This is in the technical data section of the manual, and for my device is apparently 63 samples + 7 ns
    # However I see 74 samples + 7 ns when testing this script, suggesting there is an additional delay of 11 samples
    # between the pulse generator and the AWG trigger circuitry
    print(f"Expected delay between pulse and signal: {(63 * 1 / SAMPLE_RATE_IN_HZ + 7e-9) * 1e6} microseconds")

    card.stop()
    card.disconnect()
