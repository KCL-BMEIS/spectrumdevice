import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, show
from numpy import savetxt

from pyspecde.hardware_model.spectrum_star_hub import spectrum_star_hub_factory
from pyspecde.sdk_translation_layer import (
    AcquisitionMode,
    TriggerSource,
)

# Choose configuration
device_ip = "169.254.142.75"
window_length_samples = 1000
acquisition_timeout_ms = 1000
save_output = True
save_dir = "D:\\pa_beacon_data\\"
enabled_channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

# Apply configuration
netbox = spectrum_star_hub_factory(device_ip, 2, 1)
netbox.set_enabled_channels(enabled_channels)
netbox.set_trigger_sources([TriggerSource.SPC_TMASK_SOFTWARE])
netbox.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
netbox.set_acquisition_length_samples(window_length_samples)
netbox.set_post_trigger_length_samples(window_length_samples)
netbox.set_timeout_ms(acquisition_timeout_ms)

# Execute acquisition
netbox.start_acquisition()
netbox.wait_for_acquisition_to_complete()

# Get waveform data and disconnect
netbox.set_transfer_buffer()
netbox.start_transfer()
netbox.wait_for_transfer_to_complete()
acquired_waveforms = netbox.get_waveforms()
netbox.reset()
netbox.disconnect()

# Plot waveforms
for wfm, channel_num in zip(acquired_waveforms, netbox.enabled_channels):
    plot(wfm, label=str(channel_num))
    if save_output:
        savetxt(save_dir + str(channel_num) + ".txt", wfm)  # noqa
plt.legend()
show()
