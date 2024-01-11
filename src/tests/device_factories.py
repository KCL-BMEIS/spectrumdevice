from spectrumdevice import SpectrumDigitiserStarHub
from spectrumdevice.devices.awg.awg_card import SpectrumAWGCard
from spectrumdevice.devices.awg.awg_interface import SpectrumAWGInterface
from spectrumdevice.devices.digitiser import SpectrumDigitiserCard, SpectrumDigitiserInterface
from spectrumdevice.devices.mocks import MockSpectrumAWGCard, MockSpectrumDigitiserCard, MockSpectrumDigitiserStarHub
from spectrumdevice.settings import ModelNumber
from tests.configuration import (
    MOCK_DEVICE_TEST_FRAME_RATE_HZ,
    NUM_CARDS_IN_STAR_HUB,
    NUM_CHANNELS_PER_MODULE,
    NUM_MODULES_PER_CARD,
    SINGLE_CARD_TEST_MODE,
    STAR_HUB_MASTER_CARD_INDEX,
    STAR_HUB_TEST_MODE,
    SpectrumTestMode,
    TEST_DEVICE_IP,
    TEST_DEVICE_NUMBER,
)


def create_digitiser_card_for_testing() -> SpectrumDigitiserInterface:
    """Configure a real or mock device for unit testing using the global constant values defined in
    tests/configuration.py"""
    if SINGLE_CARD_TEST_MODE == SpectrumTestMode.REAL_HARDWARE:
        return SpectrumDigitiserCard(device_number=TEST_DEVICE_NUMBER, ip_address=TEST_DEVICE_IP)
    else:
        return MockSpectrumDigitiserCard(
            device_number=TEST_DEVICE_NUMBER,
            model=ModelNumber.TYP_M2P5966_X4,
            mock_source_frame_rate_hz=MOCK_DEVICE_TEST_FRAME_RATE_HZ,
            num_modules=NUM_MODULES_PER_CARD,
            num_channels_per_module=NUM_CHANNELS_PER_MODULE,
        )


def create_awg_card_for_testing() -> SpectrumAWGInterface:
    """Configure a real or mock device for unit testing using the global constant values defined in
    tests/configuration.py"""
    if SINGLE_CARD_TEST_MODE == SpectrumTestMode.REAL_HARDWARE:
        return SpectrumAWGCard(device_number=TEST_DEVICE_NUMBER, ip_address=TEST_DEVICE_IP)
    else:
        return MockSpectrumAWGCard(
            device_number=TEST_DEVICE_NUMBER,
            model=ModelNumber.TYP_M2P6560_X4,
            num_modules=NUM_MODULES_PER_CARD,
            num_channels_per_module=NUM_CHANNELS_PER_MODULE,
        )


def create_spectrum_star_hub_for_testing() -> SpectrumDigitiserStarHub:
    """Configure a real or mock device for unit testing using the glabal constant values defined in
    tests/configuration.py"""
    if STAR_HUB_TEST_MODE == SpectrumTestMode.REAL_HARDWARE:
        child_cards = []
        for n in range(NUM_CARDS_IN_STAR_HUB):
            child_cards.append(SpectrumDigitiserCard(device_number=n, ip_address=TEST_DEVICE_IP))
        return SpectrumDigitiserStarHub(
            device_number=0, child_cards=tuple(child_cards), master_card_index=STAR_HUB_MASTER_CARD_INDEX
        )
    else:
        mock_child_cards = []
        for _ in range(NUM_CARDS_IN_STAR_HUB):
            mock_child_cards.append(
                MockSpectrumDigitiserCard(
                    device_number=0,
                    model=ModelNumber.TYP_M2P5966_X4,
                    mock_source_frame_rate_hz=MOCK_DEVICE_TEST_FRAME_RATE_HZ,
                    num_modules=NUM_MODULES_PER_CARD,
                    num_channels_per_module=NUM_CHANNELS_PER_MODULE,
                )
            )
        return MockSpectrumDigitiserStarHub(
            device_number=0, child_cards=mock_child_cards, master_card_index=STAR_HUB_MASTER_CARD_INDEX
        )
