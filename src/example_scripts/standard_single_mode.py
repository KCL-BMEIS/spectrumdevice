"""Standard Single Mode (SPC_REC_STD_SINGLE) example. The function defined here is used by the tests module as an
integration test."""

from typing import Optional

from spectrumdevice import MockSpectrumDigitiserCard, SpectrumDigitiserCard

from spectrumdevice.measurement import Measurement
from spectrumdevice.settings import (
    AcquisitionMode,
    ModelNumber,
    TriggerSource,
    ExternalTriggerMode,
    TriggerSettings,
    AcquisitionSettings,
)


def standard_single_mode_example(
    mock_mode: bool, trigger_source: TriggerSource, device_number: int, ip_address: Optional[str] = None,
        acquisition_length: int = 400
) -> Measurement:

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
        acquisition_mode=AcquisitionMode.SPC_REC_STD_SINGLE,
        sample_rate_in_hz=int(4e6),
        acquisition_length_in_samples=acquisition_length,
        pre_trigger_length_in_samples=0,
        timeout_in_ms=1000,
        enabled_channels=[0],
        vertical_ranges_in_mv=[200],
        vertical_offsets_in_percent=[0],
        timestamping_enabled=False,
    )

    # Apply settings
    card.configure_trigger(trigger_settings)
    card.configure_acquisition(acquisition_settings)

    # Execute acquisition
    meas = card.execute_standard_single_acquisition()
    card.reset()
    card.disconnect()
    return meas


if __name__ == "__main__":

    from matplotlib.pyplot import plot, show, xlabel, tight_layout, ylabel

    meas = standard_single_mode_example(
        mock_mode=False, trigger_source=TriggerSource.SPC_TMASK_EXT0, device_number=1, ip_address="169.254.142.75"
    )

    # Plot waveforms
    for waveform in meas.waveforms:
        plot(waveform)
        xlabel("Time (samples)")
        ylabel("Amplitude (Volts)")
        tight_layout()

    ts_format = "%Y-%m-%d %H:%M:%S.%f"
    print(f"Acquired {len(meas.waveforms)} waveforms with the following shapes:")
    print([wfm.shape for wfm in meas.waveforms])
    print("and the following timestamp:")
    print(meas.timestamp.strftime(ts_format) if meas.timestamp else "Timestamping disabled")

    show()
