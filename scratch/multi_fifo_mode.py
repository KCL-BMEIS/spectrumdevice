from matplotlib.pyplot import figure, plot, show
from numpy import mod

from pyspecde.hardware_model.factories import spectrum_star_hub_factory
from pyspecde.spectrum_api_wrapper import (
    AcquisitionMode,
)
from pyspecde.spectrum_api_wrapper.triggering import TriggerSource, ExternalTriggerMode

device_ip = "169.254.142.75"
window_length_seconds = 10e-6
num_measurements = 10
sample_rate_hz = 10e6
acquisition_timeout_ms = 1000
trigger_level_mv = 1000
vertical_range_mv = 200
enabled_channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

requested_length_samples = int(sample_rate_hz * window_length_seconds)
window_length_samples = int(requested_length_samples - mod(requested_length_samples, 8))

# Apply configuration
netbox = spectrum_star_hub_factory(device_ip, 2, 1)
for ch in netbox.channels:
    ch.set_vertical_range_mv(vertical_range_mv)
netbox.set_sample_rate_hz(int(sample_rate_hz))
netbox.set_enabled_channels(enabled_channels)
netbox.set_trigger_sources([TriggerSource.SPC_TMASK_EXT0])
netbox.set_external_trigger_mode(ExternalTriggerMode.SPC_TM_POS)
netbox.set_external_trigger_level_mv(trigger_level_mv)

netbox.set_acquisition_mode(AcquisitionMode.SPC_REC_FIFO_MULTI)

netbox.set_acquisition_length_samples(window_length_samples)
netbox.set_post_trigger_length_samples(window_length_samples - 8)
netbox.set_timeout_ms(acquisition_timeout_ms)

netbox.define_transfer_buffer()


# Execute acquisition
netbox.start_acquisition()
netbox.start_transfer()

all_waveform_sets = []

for _ in range(num_measurements):
    all_waveform_sets.append(netbox.get_waveforms())

netbox.stop_acquisition()
netbox.reset()
netbox.disconnect()


for waveform_set in all_waveform_sets:
    for n, waveform in enumerate(waveform_set):
        figure(n)
        plot(waveform)

show()
