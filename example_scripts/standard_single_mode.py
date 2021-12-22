from typing import List

from numpy import ndarray

from spectrumdevice import MockSpectrumCard, SpectrumCard
from spectrumdevice.settings import (
    AcquisitionMode,
    TriggerSource,
    ExternalTriggerMode,
    TriggerSettings,
    AcquisitionSettings,
)


def standard_single_mode_example(mock_mode: bool) -> List[ndarray]:

    if not mock_mode:
        # Connect to a networked device. To connect to a local (PCIe) device, do not provide an ip_address.
        DEVICE_IP_ADDRESS = "169.254.142.75"
        card = SpectrumCard(device_number=0, ip_address=DEVICE_IP_ADDRESS)
    else:
        # Set up a mock device
        card = MockSpectrumCard(
            device_number=0, mock_source_frame_rate_hz=10.0, num_modules=2, num_channels_per_module=4
        )

    # Trigger settings
    trigger_settings = TriggerSettings(
        trigger_sources=[TriggerSource.SPC_TMASK_EXT0],
        external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
        external_trigger_level_in_mv=1000,
    )

    # Acquisition settings
    acquisition_settings = AcquisitionSettings(
        acquisition_mode=AcquisitionMode.SPC_REC_STD_SINGLE,
        sample_rate_in_hz=40000000,
        acquisition_length_in_samples=400,
        pre_trigger_length_in_samples=0,
        timeout_in_ms=1000,
        enabled_channels=[0, 1, 2, 3],
        vertical_ranges_in_mv=[200, 200, 200, 200],
        vertical_offsets_in_percent=[0, 0, 0, 0],
    )

    # Apply settings
    card.configure_trigger(trigger_settings)
    card.configure_acquisition(acquisition_settings)

    # Execute acquisition
    return card.execute_standard_single_acquisition()


if __name__ == "__main__":

    from matplotlib.pyplot import plot, show

    waveforms = standard_single_mode_example(mock_mode=True)
    # Plot waveforms
    for waveform in waveforms:
        plot(waveform)

    print(f"Acquired {len(waveforms)} waveforms with the following shapes:")
    print([wfm.shape for wfm in waveforms])

    show()
