from spectrumdevice.settings import CardType
from spectrumdevice import MockSpectrumStarHub, MockSpectrumCard, SpectrumCard, SpectrumStarHub


def star_hub_example(mock_mode: bool, num_cards: int, master_card_index: int) -> SpectrumStarHub:

    if not mock_mode:
        DEVICE_IP_ADDRESS = "169.254.142.75"
        child_cards = []
        for n in range(num_cards):
            # Connect to each card in the hub.
            child_cards.append(SpectrumCard(device_number=n, ip_address=DEVICE_IP_ADDRESS))
        # Connect to the hub itself
        return SpectrumStarHub(device_number=0, child_cards=child_cards, master_card_index=master_card_index)
    else:
        mock_child_cards = []
        for n in range(num_cards):
            # Create a mock device for each card in the hub
            mock_child_cards.append(
                MockSpectrumCard(
                    device_number=n,
                    card_type=CardType.TYP_M2P5966_X4,
                    mock_source_frame_rate_hz=10.0,  # Mock devices need to be provided with a mock source frame rate
                    num_modules=2,  # (For real devices, this and num_channels_per_module are read from the hardware).
                    num_channels_per_module=4,
                )
            )
        # Create a mock hub containing the above devices
        return MockSpectrumStarHub(device_number=0, child_cards=mock_child_cards, master_card_index=master_card_index)


if __name__ == "__main__":
    hub = star_hub_example(mock_mode=True, num_cards=2, master_card_index=1)
    print(f"{hub} contains {len(hub.channels)} channels in total:")
    for channel in hub.channels:
        print(channel)
    hub.reset()
    hub.disconnect()
