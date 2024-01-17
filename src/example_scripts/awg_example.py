from time import sleep

from matplotlib.pyplot import plot, show
from numpy import int16

from spectrumdevice.devices.awg.awg_card import SpectrumAWGCard
from spectrumdevice.devices.awg.synthesis import make_full_scale_sine_waveform
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

    t, analog_wfm = make_full_scale_sine_waveform(FREQUENCY, SAMPLE_RATE, NUM_CYCLES, dtype=int16)

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
