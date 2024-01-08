from time import sleep

from numpy import array, int16, iinfo, bool_
from numpy.typing import NDArray

from spectrumdevice.devices.mocks import MockSpectrumAWGCard
from spectrumdevice.settings import (
    TriggerSettings,
    TriggerSource,
    ExternalTriggerMode,
    IOLineMode,
    ModelNumber,
    AcquisitionMode,
)
from spectrumdevice.settings.device_modes import GenerationMode
from spectrumdevice.settings.io_lines import DigOutIOLineModeSettings, DigOutSourceChannel, DigOutSourceBit

PULSE_RATE_HZ = 10
NUM_PULSES = 10


def write_digital_waveform_to_bit_15_of_analog(
    digital_waveform: NDArray[bool_], analog_waveform: NDArray[int16]
) -> NDArray[int16]:
    if analog_waveform.shape != digital_waveform.shape:
        raise ValueError("Analog and digital waveforms must have the same shape.")
    analog_waveform &= ~1  # Clear the least significant bit
    analog_waveform |= digital_waveform.astype(int16)  # Set the least significant bit using bitwise OR
    return analog_waveform


if __name__ == "__main__":

    # card = SpectrumAWGCard()
    card = MockSpectrumAWGCard(
        device_number=0,
        model=ModelNumber.TYP_M2P6560_X4,
        num_channels_per_module=1,
        num_modules=1,
        mode=AcquisitionMode.SPC_REC_STD_SINGLE,
    )
    print(card)

    trigger_settings = TriggerSettings(
        trigger_sources=[TriggerSource.SPC_TMASK_EXT0],
        external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
        external_trigger_level_in_mv=1000,
    )
    card.configure_trigger(trigger_settings)

    full_scale_min_value = iinfo(int16).min
    full_scale_max_value = iinfo(int16).max

    analog_wfm = array([0, full_scale_max_value, 0, full_scale_min_value], dtype=int16)
    digital_wfm = array([True, False, True, False])
    analog_waveform = write_digital_waveform_to_bit_15_of_analog(digital_wfm, analog_wfm)
    card.transfer_waveform(digital_wfm)
    card.set_generation_mode(GenerationMode.SPC_REP_STD_SINGLE)

    card.analog_channels[0].set_signal_amplitude_in_mv(1000)
    print(card.io_lines[0])
    card.io_lines[0].set_mode(IOLineMode.SPCM_XMODE_DIGOUT)
    card.io_lines[0].set_dig_out_settings(
        DigOutIOLineModeSettings(
            source_channel=DigOutSourceChannel.SPCM_XMODE_DIGOUTSRC_CH0,
            source_bit=DigOutSourceBit.SPCM_XMODE_DIGOUTSRC_BIT15,
        )
    )

    card.start()

    for _ in range(NUM_PULSES):
        card.force_trigger_event()
        sleep(1 / PULSE_RATE_HZ)

    card.stop()

    card.disconnect()
