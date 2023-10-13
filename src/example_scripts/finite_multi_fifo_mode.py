"""Finite Multi-FIFO mode (SPC_REC_FIFO_MULTI) example. The function defined here is used by the tests module as an
integration test."""
from typing import List, Optional

from spectrumdevice import MockSpectrumDigitiserCard, SpectrumDigitiserCard
from spectrumdevice.measurement import Measurement
from spectrumdevice.settings import (
    AcquisitionMode,
    ModelNumber,
    TriggerSource,
    ExternalTriggerMode,
    TriggerSettings,
    AcquisitionSettings,
    InputImpedance,
)


def finite_multi_fifo_example(
    mock_mode: bool,
    num_measurements: int,
    batch_size: int,
    trigger_source: TriggerSource,
    device_number: int,
    ip_address: Optional[str] = None,
    acquisition_length: int = 400,
) -> List[Measurement]:

    if not mock_mode:
        # Connect to a networked device. To connect to a local (PCIe) device, do not provide an ip_address.
        card = SpectrumDigitiserCard(device_number=device_number, ip_address=ip_address)
    else:
        # Set up a mock device
        card = MockSpectrumDigitiserCard(
            device_number=device_number,
            model=ModelNumber.TYP_M2P5966_X4,
            mock_source_frame_rate_hz=10.0,
            num_modules=2,
            num_channels_per_module=4,
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
        acquisition_length_in_samples=acquisition_length,
        pre_trigger_length_in_samples=0,
        timeout_in_ms=1000,
        enabled_channels=[0],
        vertical_ranges_in_mv=[200],
        vertical_offsets_in_percent=[0],
        input_impedances=[InputImpedance.ONE_MEGA_OHM],
        timestamping_enabled=True,
        batch_size=batch_size,
    )

    # Apply settings
    card.configure_trigger(trigger_settings)
    card.configure_acquisition(acquisition_settings)

    # Execute acquisition
    measurements = card.execute_finite_fifo_acquisition(num_measurements)
    card.reset()
    card.disconnect()
    return measurements


if __name__ == "__main__":

    from matplotlib.pyplot import plot, show, figure, title

    # Only a few parameters are included as arguments here. See contents of the example function for other settings
    measurements = finite_multi_fifo_example(
        mock_mode=False,
        num_measurements=10,  # number of waveforms to acquire from each enabled channel
        batch_size=5,  # number of measurements to acquire before they are returned by get_waveforms()
        trigger_source=TriggerSource.SPC_TMASK_EXT0,
        device_number=1,
        ip_address="169.254.13.35",
    )

    # Plot waveforms
    for n, measurement in enumerate(measurements):
        figure()
        title(f"Measurement {n}")
        for wfm in measurement.waveforms:
            plot(wfm)

    ts_format = "%Y-%m-%d %H:%M:%S.%f"
    print(f"Completed {len(measurements)} measurements each containing {len(measurements[0].waveforms)} waveforms.")
    print(f"Waveforms had the following shape: {measurements[0].waveforms[0].shape}")
    print(f"and the following timestamps:")
    for measurement in measurements:
        print(measurement.timestamp.strftime(ts_format) if measurement.timestamp else "Timestamping disabled")

    show()
