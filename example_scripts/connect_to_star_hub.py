from pyspecde.hardware_model.mock_spectrum_hardware import MockSpectrumStarHub, MockSpectrumCard
from pyspecde.hardware_model.spectrum_card import SpectrumCard
from pyspecde.hardware_model.spectrum_star_hub import SpectrumStarHub

if __name__ == "__main__":

    MOCK_MODE = True  # Set to false to connect to real hardware
    NUM_CARDS_IN_STAR_HUB = 2
    STAR_HUB_MASTER_CARD_INDEX = 1  # Index (0+) of the card controlling the clock. This is usually hard-wired.

    if not MOCK_MODE:
        DEVICE_IP_ADDRESS = "169.254.142.75"
        child_cards = []
        for n in range(NUM_CARDS_IN_STAR_HUB):
            # Connect to each card in the hub.
            child_cards.append(SpectrumCard(device_number=n, ip_address=DEVICE_IP_ADDRESS))
        # Connect to the hub itself
        hub = SpectrumStarHub(device_number=0, child_cards=child_cards, master_card_index=STAR_HUB_MASTER_CARD_INDEX)
    else:
        mock_child_cards = []
        for _ in range(NUM_CARDS_IN_STAR_HUB):
            # Create a mock device for each card in the hub
            mock_child_cards.append(
                MockSpectrumCard(
                    mock_source_frame_rate_hz=10.0,  # Mock devices need to be provided with a mock source frame rate
                    num_modules=2,  # (For real devices, this and num_channels_per_module are read from the hardware).
                    num_channels_per_module=4,
                )
            )
        # Create a mock hub containing the above devices
        hub = MockSpectrumStarHub(child_cards=mock_child_cards, master_card_index=STAR_HUB_MASTER_CARD_INDEX)

    print(f"The hub contains {len(hub.channels)} channels in total.")
    hub.disconnect()
