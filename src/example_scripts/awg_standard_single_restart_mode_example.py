from time import sleep

from numpy import int16

from spectrumdevice.devices.awg.awg_card import SpectrumAWGCard
from spectrumdevice.devices.awg.synthesis import make_full_scale_sine_waveform
from spectrumdevice.devices.mocks import MockSpectrumAWGCard
from spectrumdevice.settings import (
    TriggerSettings,
    TriggerSource,
    GenerationSettings,
    OutputChannelFilter,
    ModelNumber,
)
from spectrumdevice.settings.channel import OutputChannelStopLevelMode
from spectrumdevice.settings.device_modes import GenerationMode

PULSE_RATE_HZ = 200
NUM_TRANSMISSIONS = 5
NUM_CYCLES_PER_TRANSMISSION = 3
FREQUENCY_HZ = 1e3
AMPLITUDE_V = 1.0
SAMPLE_RATE = 125000000


def awg_single_restart_mode_example(mock_mode: bool) -> None:

    # create a connection to a mock or real AWG card
    if not mock_mode:
        card = SpectrumAWGCard(device_number=0)
    else:
        card = MockSpectrumAWGCard(
            device_number=0, model=ModelNumber.TYP_M2P6560_X4, num_modules=1, num_channels_per_module=1
        )

    sample_rate_in_hz = SAMPLE_RATE
    number_of_generations = NUM_TRANSMISSIONS

    # create a waveform to generate
    t, analog_wfm = make_full_scale_sine_waveform(
        frequency_in_hz=FREQUENCY_HZ,
        sample_rate_in_hz=sample_rate_in_hz,
        num_cycles=NUM_CYCLES_PER_TRANSMISSION,
        dtype=int16,
    )

    # configure signal generation
    generation_settings = GenerationSettings(
        generation_mode=GenerationMode.SPC_REP_STD_SINGLERESTART,
        waveform=analog_wfm,
        sample_rate_in_hz=sample_rate_in_hz,
        num_loops=number_of_generations,
        enabled_channels=[0],
        signal_amplitudes_in_mv=[int(round((AMPLITUDE_V * 1000)))],
        dc_offsets_in_mv=[0],
        output_filters=[OutputChannelFilter.LOW_PASS_70_MHZ],
        stop_level_modes=[OutputChannelStopLevelMode.SPCM_STOPLVL_ZERO],
    )
    card.configure_generation(generation_settings)

    # configure triggering (here we configure an external trigger, but actually we will be forcing
    # the trigger event to occur from software on line 72)
    trigger_settings = TriggerSettings(
        trigger_sources=[TriggerSource.SPC_TMASK_EXT0],
    )
    card.configure_trigger(trigger_settings)

    # start the card and then force a trigger for each generation we want to perform
    # we are using GenerationMode.SPC_REP_STD_SINGLERESTART so the whole waveform will be generated each time the card
    # is trigger, until "num_loops" triggers have been detected.
    card.start()

    # force triggers at the requested rate. Remove if real external trigger present.
    for _ in range(number_of_generations):
        card.force_trigger()
        sleep(1 / PULSE_RATE_HZ)
        print("generated pulse")
    card.stop()
    card.disconnect()


if __name__ == "__main__":
    # change mock_mode to False to connect to a real card
    awg_single_restart_mode_example(mock_mode=True)
