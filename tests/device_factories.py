from spectrumdevice.settings import CardType
from spectrumdevice.devices.mocks.mock_devices import MockSpectrumCard, MockSpectrumStarHub
from spectrumdevice.devices.spectrum_card import SpectrumCard
from spectrumdevice.devices.spectrum_star_hub import SpectrumStarHub
from tests.configuration import (
    TEST_DEVICE_IP,
    MOCK_DEVICE_TEST_FRAME_RATE_HZ,
    NUM_MODULES_PER_CARD,
    NUM_CHANNELS_PER_MODULE,
    NUM_CARDS_IN_STAR_HUB,
    STAR_HUB_MASTER_CARD_INDEX,
    SpectrumTestMode,
    SINGLE_CARD_TEST_MODE,
    STAR_HUB_TEST_MODE,
    TEST_DEVICE_NUMBER,
)


def create_spectrum_card_for_testing() -> SpectrumCard:
    """Configure a real or mock device for unit testing using the glabal constant values defined in
    tests/configuration.py"""
    if SINGLE_CARD_TEST_MODE == SpectrumTestMode.REAL_HARDWARE:
        return SpectrumCard(device_number=TEST_DEVICE_NUMBER, ip_address=TEST_DEVICE_IP)
    else:
        return MockSpectrumCard(
            device_number=TEST_DEVICE_NUMBER,
            card_type=CardType.TYP_M2P5966_X4,
            mock_source_frame_rate_hz=MOCK_DEVICE_TEST_FRAME_RATE_HZ,
            num_modules=NUM_MODULES_PER_CARD,
            num_channels_per_module=NUM_CHANNELS_PER_MODULE,
        )


def create_spectrum_star_hub_for_testing() -> SpectrumStarHub:
    """Configure a real or mock device for unit testing using the glabal constant values defined in
    tests/configuration.py"""
    if STAR_HUB_TEST_MODE == SpectrumTestMode.REAL_HARDWARE:
        child_cards = []
        for n in range(NUM_CARDS_IN_STAR_HUB):
            child_cards.append(SpectrumCard(device_number=n, ip_address=TEST_DEVICE_IP))
        return SpectrumStarHub(device_number=0, child_cards=child_cards, master_card_index=STAR_HUB_MASTER_CARD_INDEX)
    else:
        mock_child_cards = []
        for _ in range(NUM_CARDS_IN_STAR_HUB):
            mock_child_cards.append(
                MockSpectrumCard(
                    device_number=0,
                    card_type=CardType.TYP_M2P5966_X4,
                    mock_source_frame_rate_hz=MOCK_DEVICE_TEST_FRAME_RATE_HZ,
                    num_modules=NUM_MODULES_PER_CARD,
                    num_channels_per_module=NUM_CHANNELS_PER_MODULE,
                )
            )
        return MockSpectrumStarHub(
            device_number=0, child_cards=mock_child_cards, master_card_index=STAR_HUB_MASTER_CARD_INDEX
        )
