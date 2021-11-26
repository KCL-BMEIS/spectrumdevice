import matplotlib.pyplot as plt
from matplotlib import figure
from matplotlib.pyplot import plot, show
from numpy import arange, savetxt

from pyspecde.hardware_model.spectrum_star_hub import spectrum_star_hub_factory
from pyspecde.sdk_translation_layer import (
    AcquisitionMode,
    ExternalTriggerMode, TriggerSource,
)

# Choose configuration
device_ip = "169.254.142.75"
window_length_seconds = 10e-6
sample_rate_hz = 40e6
acquisition_timeout_ms = 1000
trigger_level_mv = 1000
vertical_range_mv = 200
save_output = True
save_dir = "C:\\3d_unt_pa_beacon\\"
enabled_channels = [8, 16]  #, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

window_length_samples = int(sample_rate_hz * window_length_seconds)

# Apply configuration
netbox = spectrum_star_hub_factory(device_ip, 2, 1)
for ch in netbox.channels:
    ch.set_vertical_range_mv(vertical_range_mv)
netbox.set_sample_rate_hz(int(sample_rate_hz))
netbox.set_enabled_channels(enabled_channels)
netbox.set_trigger_sources([TriggerSource.SPC_TMASK_EXT0])
netbox.set_external_trigger_mode(ExternalTriggerMode.SPC_TM_POS)
netbox.set_external_trigger_level_mv(trigger_level_mv)
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
    t = 1e6 * arange(len(wfm)) * (1 / sample_rate_hz)
    plt.figure()
    plot(t[100:], wfm[100:], label=str(channel_num))
    plt.xlabel('Time (us)')
    if save_output:
        savetxt(save_dir + str(channel_num) + ".txt", wfm)  # noqa
plt.legend()
show()
