from time import sleep

from numpy import array, int16, iinfo

from spectrumdevice.devices.awg.awg_card import SpectrumAWGCard
from spectrumdevice.settings import TriggerSettings, TriggerSource, ExternalTriggerMode
from spectrumdevice.settings.device_modes import GenerationMode

PULSE_RATE_HZ = 10
NUM_PULSES = 10

if __name__ == "__main__":

    card = SpectrumAWGCard()
    print(card)

    trigger_settings = TriggerSettings(
        trigger_sources=[TriggerSource.SPC_TMASK_EXT0],
        external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
        external_trigger_level_in_mv=1000,
    )
    card.configure_trigger(trigger_settings)

    full_scale_min_value = iinfo(int16).min
    full_scale_max_value = iinfo(int16).max

    wfm = array([0, full_scale_max_value, 0, full_scale_min_value], dtype=int16)
    card.transfer_waveform(wfm)
    card.set_generation_mode(GenerationMode.SPC_REP_STD_SINGLE)

    card.channels[0].set_signal_amplitude_in_mv(1000)

    card.start()

    for _ in range(NUM_PULSES):
        card.force_trigger_event()
        sleep(1 / PULSE_RATE_HZ)

    card.stop()

    card.disconnect()
