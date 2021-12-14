from matplotlib.pyplot import plot, show, figure

from pyspecde.hardware_model.mock_spectrum_hardware import MockSpectrumCard
from pyspecde.spectrum_api_wrapper import AcquisitionMode

card = MockSpectrumCard()

card.set_acquisition_mode(AcquisitionMode.SPC_REC_FIFO_MULTI)
card.set_acquisition_length_samples(1000)
card.set_post_trigger_length_samples(1000)
card.set_enabled_channels([0, 1, 2, 3, 4, 5, 6, 7])

card.define_transfer_buffer()

# Execute acquisition
card.start_acquisition()
card.start_transfer()

all_waveform_sets = []

for _ in range(5):
    all_waveform_sets.append(card.get_waveforms())

card.stop_acquisition()

for waveform_set in all_waveform_sets:
    figure()
    for waveform in waveform_set:
        plot(waveform)

show()
