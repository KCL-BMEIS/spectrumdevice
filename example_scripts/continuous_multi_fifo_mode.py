"""Continuous Multi-FIFO mode (SPC_REC_FIFO_MULTI) example. The function defined here is used by the tests module as an
integration test."""
from time import monotonic
from typing import List, Optional

from numpy import ndarray

from spectrumdevice import MockSpectrumCard, SpectrumCard
from spectrumdevice.settings import (
    AcquisitionMode,
    TriggerSource,
    ExternalTriggerMode,
    TriggerSettings,
    AcquisitionSettings,
)


def continuous_multi_fifo_example(mock_mode: bool, acquisition_duration_in_seconds: float,
                                  trigger_source: TriggerSource, ip_address: Optional[str] = None)\
        -> List[List[ndarray]]:

    if not mock_mode:
        # Connect to a networked device. To connect to a local (PCIe) device, do not provide an ip_address.
        card = SpectrumCard(device_number=0, ip_address=ip_address)
    else:
        # Set up a mock device
        card = MockSpectrumCard(
            device_number=0, mock_source_frame_rate_hz=1.0, num_modules=2, num_channels_per_module=4
        )

    # Trigger settings
    trigger_settings = TriggerSettings(
        trigger_sources=[trigger_source],
        external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
        external_trigger_level_in_mv=1000,
    )

    # Acquisition settings
    acquisition_settings = AcquisitionSettings(
        acquisition_mode=AcquisitionMode.SPC_REC_FIFO_MULTI,
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
    start_time = monotonic()
    card.execute_continuous_multi_fifo_acquisition()

    # Retrieve streamed waveform data until desired time has elapsed
    measurements = []
    while (monotonic() - start_time) < acquisition_duration_in_seconds:
        measurements.append(card.get_waveforms())

    # Stop the acquisition (and streaming)
    card.stop_acquisition()

    return measurements


if __name__ == "__main__":

    from matplotlib.pyplot import plot, show, figure, title

    measurements = continuous_multi_fifo_example(mock_mode=True, acquisition_duration_in_seconds=4.0,
                                                 trigger_source=TriggerSource.SPC_TMASK_EXT0)

    # Plot waveforms
    for n, measurement in enumerate(measurements):
        figure()
        title(f"Measurement {n}")
        for waveform in measurement:
            plot(waveform)

    print(f"Completed {len(measurements)} measurements each containing {len(measurements[0])} waveforms.")
    print(f"Waveforms had the following shape: {measurements[0][0].shape}")

    show()
