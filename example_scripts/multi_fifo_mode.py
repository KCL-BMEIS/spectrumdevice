from matplotlib.pyplot import plot, show, figure, title

from pyspecde.hardware_model.mock_spectrum_hardware import MockSpectrumCard
from pyspecde.hardware_model.spectrum_card import SpectrumCard
from pyspecde.spectrum_api_wrapper import AcquisitionMode
from pyspecde.spectrum_api_wrapper.triggering import TriggerSource, ExternalTriggerMode

# Set to false to connect to real hardware
MOCK_MODE = True
NUM_ACQUISITIONS = 2

if not MOCK_MODE:
    # Connect to a networked device. To connect to a local (PCIe) device, do not provide an ip_address.
    DEVICE_IP_ADDRESS = "169.254.142.75"
    card = SpectrumCard(device_number=0, ip_address=DEVICE_IP_ADDRESS)
else:
    # Set up a mock device
    card = MockSpectrumCard(device_number=0, mock_source_frame_rate_hz=10.0, num_modules=2, num_channels_per_module=4)

# User settings
window_length_seconds = 10e-6
num_averages = 10
plot_crop_seconds = 1e-6
sample_rate_hz = 40e6
acquisition_timeout_ms = 1000
trigger_level_mv = 1000
vertical_range_mv = 200
enabled_channels = [0, 1, 2, 3]

# Configure spectrum device
window_length_samples = int(sample_rate_hz * window_length_seconds)
card.set_acquisition_mode(AcquisitionMode.SPC_REC_FIFO_MULTI)
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

# Start acquisitions
card.define_transfer_buffer()
card.start_acquisition()
card.start_transfer()

# Wait for each acquisition's data to arrive
acquisitions = []
for _ in range(NUM_ACQUISITIONS):
    acquisitions.append(card.get_waveforms())
card.stop_acquisition()

# Plot waveforms
for n, acquisition in enumerate(acquisitions):
    figure()
    title(f"Acquisition {n}")
    for waveform in acquisition:
        plot(waveform)

print(f"Completed {len(acquisitions)} acquisitions each containing {len(acquisitions[0])} waveforms.")
print(f"Waveforms had the following shape: {acquisitions[0][0].shape}")

show()
