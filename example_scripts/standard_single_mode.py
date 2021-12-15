from matplotlib.pyplot import plot, show

from pyspecde.hardware_model.mock_spectrum_hardware import mock_spectrum_card_factory
from pyspecde.hardware_model.spectrum_card import SpectrumCardConfig, spectrum_card_factory
from pyspecde.spectrum_api_wrapper import AcquisitionMode
from pyspecde.spectrum_api_wrapper.triggering import TriggerSource, ExternalTriggerMode

MOCK_MODE = True

# User settings
config = SpectrumCardConfig(ip_address="169.254.142.75", visa_device_num=0, num_modules=2, num_channels_per_module=8)
window_length_seconds = 10e-6
num_averages = 10
plot_crop_seconds = 1e-6
sample_rate_hz = 40e6
acquisition_timeout_ms = 1000
trigger_level_mv = 1000
vertical_range_mv = 200
enabled_channels = [0, 1, 2, 3]

# Create spectrum device
if MOCK_MODE:
    card = mock_spectrum_card_factory(config, frame_rate_hz=10.0)
else:
    card = spectrum_card_factory(config)

# Configure spectrum device
window_length_samples = int(sample_rate_hz * window_length_seconds)
card.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
card.set_sample_rate_hz(int(sample_rate_hz))
card.set_acquisition_length_samples(window_length_samples)
card.set_post_trigger_length_samples(window_length_samples)
card.set_enabled_channels(enabled_channels)
card.set_trigger_sources([TriggerSource.SPC_TMASK_EXT0])
card.set_external_trigger_mode(ExternalTriggerMode.SPC_TM_POS)
card.set_external_trigger_level_mv(trigger_level_mv)
card.set_timeout_ms(acquisition_timeout_ms)
for ch in card.channels:
    ch.set_vertical_range_mv(vertical_range_mv)

# Execute acquisition
card.start_acquisition()
card.wait_for_acquisition_to_complete()

# Get waveform data
card.define_transfer_buffer()
card.start_transfer()
card.wait_for_transfer_to_complete()
waveforms = card.get_waveforms()

# Plot waveforms
for waveform in waveforms:
    plot(waveform)

print(f'Acquired {len(waveforms)} waveforms with the following shapes:')
print([wfm.shape for wfm in waveforms])

show()
