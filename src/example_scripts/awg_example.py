from time import sleep

from matplotlib.pyplot import plot, show
from numpy import array, int16, iinfo, bool_, linspace, sin, pi
from numpy.typing import NDArray

from spectrumdevice import SpectrumDigitiserCard
from spectrumdevice.devices.awg.awg_card import SpectrumAWGCard
from spectrumdevice.devices.mocks import MockSpectrumAWGCard
from spectrumdevice.settings import (
    TriggerSettings,
    TriggerSource,
    ExternalTriggerMode,
    IOLineMode,
    ModelNumber,
    AcquisitionMode, AcquisitionSettings, InputImpedance,
)
from spectrumdevice.settings.channel import OutputChannelStopLevelMode
from spectrumdevice.settings.device_modes import GenerationMode
from spectrumdevice.settings.io_lines import DigOutIOLineModeSettings, DigOutSourceChannel, DigOutSourceBit

PULSE_RATE_HZ = 5000
NUM_PULSES = 5
NUM_CYCLES = 2
FREQUENCY = 20e3
SAMPLE_RATE = 125000000


def write_digital_waveform_to_bit_15_of_analog(
    digital_waveform: NDArray[bool_], analog_waveform: NDArray[int16]
) -> NDArray[int16]:
    if analog_waveform.shape != digital_waveform.shape:
        raise ValueError("Analog and digital waveforms must have the same shape.")
    analog_waveform &= ~1  # Clear the least significant bit
    analog_waveform |= digital_waveform.astype(int16)  # Set the least significant bit using bitwise OR
    return analog_waveform


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

    waveforms = []
    for _ in range(NUM_PULSES):
        card.force_trigger_event()
        sleep(1 / PULSE_RATE_HZ)
        print("generated pulse")


    card.stop()
    card.disconnect()

    plot(t * 1e6, analog_wfm)
    show()


    # card = MockSpectrumAWGCard(
    #     device_number=0,
    #     model=ModelNumber.TYP_M2P6560_X4,
    #     num_channels_per_module=1,
    #     num_modules=1,
    #     mode=AcquisitionMode.SPC_REC_STD_SINGLE,
    # )

    # digitiser = SpectrumDigitiserCard(device_number=1, ip_address="169.254.13.35")
    # digitiser_trigger = TriggerSettings(
    #     trigger_sources=[TriggerSource.SPC_TMASK_EXT0],
    #     external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
    #     external_trigger_level_in_mv=1000,
    # )
    # digitiser_settings = AcquisitionSettings(
    #     acquisition_mode=AcquisitionMode.SPC_REC_FIFO_MULTI,
    #     sample_rate_in_hz=1000000,
    #     acquisition_length_in_samples=400,
    #     pre_trigger_length_in_samples=0,
    #     timeout_in_ms=1000,
    #     enabled_channels=[0],
    #     vertical_ranges_in_mv=[200],
    #     vertical_offsets_in_percent=[0],
    #     input_impedances=[InputImpedance.ONE_MEGA_OHM],
    #     timestamping_enabled=False,
    # )
    # digitiser.configure_trigger(digitiser_trigger)
    # digitiser.configure_acquisition(digitiser_settings)

    # print(digitiser)

    # analog_wfm = array([0, full_scale_max_value, 0, full_scale_min_value], dtype=int16)
    # digital_wfm = array([True, False, True, False])
    # analog_waveform = write_digital_waveform_to_bit_15_of_analog(digital_wfm, analog_wfm)
    # print(card.io_lines[0])
    # card.io_lines[0].set_mode(IOLineMode.SPCM_XMODE_DIGOUT)
    # card.io_lines[0].set_dig_out_settings(
    #     DigOutIOLineModeSettings(
    #         source_channel=DigOutSourceChannel.SPCM_XMODE_DIGOUTSRC_CH0,
    #         source_bit=DigOutSourceBit.SPCM_XMODE_DIGOUTSRC_BIT15,
    #     )
    # )
    # digitiser.stop()

    # digitiser.execute_continuous_fifo_acquisition()

    # waveforms = waveforms + digitiser.get_waveforms()

    # digitiser.reset()
    # digitiser.disconnect()
