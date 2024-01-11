from time import sleep

from matplotlib.pyplot import plot, show
from numpy import int16, iinfo, linspace, sin, pi

from spectrumdevice.devices.awg.awg_card import SpectrumAWGCard
from spectrumdevice.settings import TriggerSettings, TriggerSource, ExternalTriggerMode
from spectrumdevice.settings.channel import OutputChannelStopLevelMode
from spectrumdevice.settings.device_modes import GenerationMode

PULSE_RATE_HZ = 5000
NUM_PULSES = 5
NUM_CYCLES = 2
FREQUENCY = 20e3
SAMPLE_RATE = 125000000


if __name__ == "__main__":

    card = SpectrumAWGCard(device_number=0)
    print(card)

    trigger_settings = TriggerSettings(
        trigger_sources=[TriggerSource.SPC_TMASK_EXT0],
        external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
        external_trigger_level_in_mv=200,
    )
    card.configure_trigger(trigger_settings)

    full_scale_min_value = iinfo(int16).min
    full_scale_max_value = iinfo(int16).max

    duration = NUM_CYCLES / FREQUENCY
    t = linspace(0, duration, int(duration * SAMPLE_RATE + 1))
    analog_wfm = (sin(2 * pi * FREQUENCY * t) * full_scale_max_value).astype(int16)
    card.set_sample_rate_in_hz(SAMPLE_RATE)
    card.set_generation_mode(GenerationMode.SPC_REP_STD_SINGLERESTART)
    card.set_num_loops(NUM_PULSES)
    card.transfer_waveform(analog_wfm)
    card.analog_channels[0].set_stop_level_mode(OutputChannelStopLevelMode.SPCM_STOPLVL_ZERO)
    card.analog_channels[0].set_is_switched_on(True)
    card.analog_channels[0].set_signal_amplitude_in_mv(1000)

    card.start()

    for _ in range(NUM_PULSES):
        card.force_trigger_event()
        sleep(1 / PULSE_RATE_HZ)
        print("generated pulse")

    card.stop()
    card.disconnect()

    plot(t * 1e6, analog_wfm)
    show()
