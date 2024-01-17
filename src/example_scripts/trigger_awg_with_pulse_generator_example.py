from time import sleep

from numpy import int16

from spectrumdevice.devices.awg.awg_card import SpectrumAWGCard
from spectrumdevice.devices.awg.synthesis import make_full_scale_sine_waveform
from spectrumdevice.settings import TriggerSettings, TriggerSource, ExternalTriggerMode, IOLineMode
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


SAMPLE_RATE = 40000000


if __name__ == "__main__":

    card = SpectrumAWGCard(device_number=0)

    card_trigger_settings = TriggerSettings(
        trigger_sources=[TriggerSource.SPC_TMASK_EXT2],  # ext1 trigger source is first IOLine
        external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
    )

    t, analog_wfm = make_full_scale_sine_waveform(
        frequency_in_hz=1e6, sample_rate_hz=SAMPLE_RATE, num_cycles=1, dtype=int16
    )

    # Set up AWG card
    card.configure_trigger(card_trigger_settings)
    card.set_sample_rate_in_hz(SAMPLE_RATE)
    card.set_generation_mode(GenerationMode.SPC_REP_STD_SINGLERESTART)
    card.set_num_loops(1)
    card.transfer_waveform(analog_wfm)
    card.analog_channels[0].set_stop_level_mode(OutputChannelStopLevelMode.SPCM_STOPLVL_ZERO)
    card.analog_channels[0].set_is_switched_on(True)
    card.analog_channels[0].set_signal_amplitude_in_mv(1000)

    pulse_trigger_settings = PulseGeneratorTriggerSettings(
        trigger_mode=PulseGeneratorTriggerMode.SPCM_PULSEGEN_MODE_SINGLESHOT,
        trigger_detection_mode=PulseGeneratorTriggerDetectionMode.RISING_EDGE,
        multiplexer_1_source=PulseGeneratorMultiplexer1TriggerSource.SPCM_PULSEGEN_MUX1_SRC_UNUSED,
        multiplexer_1_output_inversion=False,
        multiplexer_2_source=PulseGeneratorMultiplexer2TriggerSource.SPCM_PULSEGEN_MUX2_SRC_SOFTWARE,
        multiplexer_2_output_inversion=False,
    )

    pulse_output_settings = PulseGeneratorOutputSettings(
        period_in_seconds=1e-3, duty_cycle=0.5, num_pulses=10, delay_in_seconds=0.0, output_inversion=False
    )

    card.io_lines[0].set_mode(IOLineMode.SPCM_XMODE_PULSEGEN)
    card.io_lines[0].pulse_generator.configure_trigger(pulse_trigger_settings)
    card.io_lines[0].pulse_generator.configure_output(pulse_output_settings)

    card.start()

    card.io_lines[0].pulse_generator.force_trigger()
    sleep(1)
    card.stop()
    card.disconnect()
