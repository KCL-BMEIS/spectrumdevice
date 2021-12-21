import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, show
from numpy import arange, mean, savetxt, stack

from pyspecde.devices.factories import spectrum_star_hub_factory
from pyspecde import AcquisitionMode
from pyspecde.settings.triggering import TriggerSource, ExternalTriggerMode

# Choose configuration
from spectrum_gmbh.regs import (
    SPC_50OHM0,
    SPC_50OHM1,
    SPC_50OHM2,
    SPC_50OHM3,
    SPC_50OHM4,
    SPC_50OHM5,
    SPC_50OHM6,
    SPC_50OHM7,
)

device_ip = "169.254.142.75"
window_length_seconds = 10e-6
num_averages = 10
plot_crop_seconds = 1e-6
sample_rate_hz = 40e6
acquisition_timeout_ms = 1000
trigger_level_mv = 1000
vertical_range_mv = 200
save_output = True
save_dir = "C:\\3d_unt_pa_beacon\\mengjie_lab_261121\\translated_25_mm\\0 degrees\\2_z=10mm_translation=10mm_5.5kHz_aligned_1024avgs\\"
enabled_channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

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

netbox._child_cards[0].write_to_spectrum_device_register(SPC_50OHM0, 0)
netbox._child_cards[0].write_to_spectrum_device_register(SPC_50OHM1, 0)
netbox._child_cards[0].write_to_spectrum_device_register(SPC_50OHM2, 0)
netbox._child_cards[0].write_to_spectrum_device_register(SPC_50OHM3, 0)
netbox._child_cards[0].write_to_spectrum_device_register(SPC_50OHM4, 0)
netbox._child_cards[0].write_to_spectrum_device_register(SPC_50OHM5, 0)
netbox._child_cards[0].write_to_spectrum_device_register(SPC_50OHM6, 0)
netbox._child_cards[0].write_to_spectrum_device_register(SPC_50OHM7, 0)

netbox._child_cards[1].write_to_spectrum_device_register(SPC_50OHM0, 0)
netbox._child_cards[1].write_to_spectrum_device_register(SPC_50OHM1, 0)
netbox._child_cards[1].write_to_spectrum_device_register(SPC_50OHM2, 0)
netbox._child_cards[1].write_to_spectrum_device_register(SPC_50OHM3, 0)
netbox._child_cards[1].write_to_spectrum_device_register(SPC_50OHM4, 0)
netbox._child_cards[1].write_to_spectrum_device_register(SPC_50OHM5, 0)
netbox._child_cards[1].write_to_spectrum_device_register(SPC_50OHM6, 0)
netbox._child_cards[1].write_to_spectrum_device_register(SPC_50OHM7, 0)

all_waveforms = []

for repeat_index in range(num_averages):
    # Execute acquisition
    netbox.start_acquisition()
    netbox.wait_for_acquisition_to_complete()

    # Get waveform data
    netbox.define_transfer_buffer()
    netbox.start_transfer()
    netbox.wait_for_transfer_to_complete()
    waveforms = netbox.get_waveforms()

    if save_output:
        for wfm, channel_num in zip(waveforms, netbox.enabled_channels):
            savetxt(save_dir + f"Channel_{channel_num:02d}_repeat_{repeat_index:03d}.txt", wfm)  # type: ignore

    all_waveforms.append(waveforms)

mean_waveforms = mean([stack(wfms) for wfms in all_waveforms], axis=0)

# disconnect
netbox.reset()
netbox.disconnect()

# Plot waveforms
for wfm, channel_num in zip(mean_waveforms, netbox.enabled_channels):
    dt = 1 / sample_rate_hz
    plot_crop_samples = int(plot_crop_seconds / dt)
    t = 1e6 * arange(len(wfm)) * dt
    plt.figure()
    plot(t[plot_crop_samples:], wfm[plot_crop_samples:], label=str(channel_num))
    plt.xlabel("Time (us)")
# plt.legend()
show()
