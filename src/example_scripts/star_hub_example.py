from matplotlib.pyplot import figure, title, plot, show

from spectrumdevice.devices.mocks import MockSpectrumDigitiserCard, MockSpectrumDigitiserStarHub
from spectrumdevice.devices.digitiser import SpectrumDigitiserCard
from spectrumdevice.devices.digitiser import SpectrumDigitiserStarHub
from spectrumdevice.settings import (
    ModelNumber,
    TriggerSettings,
    TriggerSource,
    ExternalTriggerMode,
    AcquisitionMode,
    AcquisitionSettings,
)


def connect_to_star_hub_example(
    mock_mode: bool, num_cards: int, master_card_index: int, ip_address: str
) -> SpectrumDigitiserStarHub:

    if not mock_mode:
        child_cards = []
        for n in range(num_cards):
            # Connect to each card in the hub.
            child_cards.append(SpectrumDigitiserCard(device_number=n, ip_address=ip_address))
        # Connect to the hub itself
        return SpectrumDigitiserStarHub(device_number=0, child_cards=child_cards, master_card_index=master_card_index)
    else:
        mock_child_cards = []
        for n in range(num_cards):
            # Create a mock device for each card in the hub
            mock_child_cards.append(
                MockSpectrumDigitiserCard(
                    device_number=n,
                    model=ModelNumber.TYP_M2P5966_X4,
                    mock_source_frame_rate_hz=10.0,  # Mock devices need to be provided with a mock source frame rate
                    num_modules=2,  # (For real devices, this and num_channels_per_module are read from the hardware).
                    num_channels_per_module=4,
                )
            )
        # Create a mock hub containing the above devices
        return MockSpectrumDigitiserStarHub(
            device_number=0, child_cards=mock_child_cards, master_card_index=master_card_index
        )


if __name__ == "__main__":

    num_measurements = 5

    hub = connect_to_star_hub_example(mock_mode=False, num_cards=2, master_card_index=1, ip_address="169.254.13.35")

    print(f"{hub} contains {len(hub.channels)} channels in total:")
    for channel in hub.channels:
        print(channel)

    # Trigger settings
    trigger_settings = TriggerSettings(
        trigger_sources=[TriggerSource.SPC_TMASK_EXT0],
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
        enabled_channels=[0, 8],  # at least 1 channel from each child card must be enabled
        vertical_ranges_in_mv=[200],
        vertical_offsets_in_percent=[0],
        timestamping_enabled=True,
        batch_size=5,
    )

    # Apply settings
    hub.configure_trigger(trigger_settings)
    hub.configure_acquisition(acquisition_settings)

    # Execute acquisition
    measurements = hub.execute_finite_fifo_acquisition(num_measurements)

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

    hub.reset()
    hub.disconnect()

    show()
