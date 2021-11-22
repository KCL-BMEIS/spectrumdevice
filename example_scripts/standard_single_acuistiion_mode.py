from matplotlib.pyplot import plot, show

from pyspecde.hardware_model.spectrum_card import spectrum_card_factory
from pyspecde.hardware_model.spectrum_star_hub import create_visa_string_from_ip
from pyspecde.sdk_translation_layer import (
    AcquisitionMode,
    ExternalTriggerMode, TriggerSource, transfer_buffer_factory,
)

device_ip = "169.254.142.75"

window_length_samples = 16384
bit_depth = 16
acquisition_timeout_ms = 1000

window_length_bytes = window_length_samples * (window_length_samples / 8)

card = spectrum_card_factory(create_visa_string_from_ip(ip_address=device_ip, instrument_number=1))

card.set_enabled_channels([0, 1])

card.set_trigger_sources([TriggerSource.SPC_TMASK_EXT0])
card.set_external_trigger_mode(ExternalTriggerMode.SPC_TM_POS)
card.set_external_trigger_level_mv(1000)

card.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
card.set_acquisition_length_samples(window_length_samples)
card.set_post_trigger_length_samples(window_length_samples)
card.set_timeout_ms(acquisition_timeout_ms)

card.start_acquisition()
card.wait_for_acquisition_to_complete()

transfer_buffer = transfer_buffer_factory(window_length_samples * len(card.enabled_channels))

card.set_transfer_buffer(transfer_buffer)
card.start_transfer()
card.wait_for_transfer_to_complete()

acquired_waveform = card.transfer_buffer.data_buffer
plot(acquired_waveform)

card.disconnect()

show()
