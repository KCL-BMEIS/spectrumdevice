from enum import Enum

from pyspecde.spectrum_api_wrapper import SPECTRUM_DRIVERS_FOUND
from pyspecde.exceptions import SpectrumIOError


class SpectrumTestMode(Enum):
    MOCK_HARDWARE = 0
    REAL_HARDWARE = 1


# Set to TestMode.MOCK_HARDWARE for software-only testing, even if Spectrum drivers are found on the system
# Set to TestMode.REAL_HARDWARE to run tests on a real hardware device as configured below.
SINGLE_CARD_TEST_MODE = SpectrumTestMode.MOCK_HARDWARE
STAR_HUB_TEST_MODE = SpectrumTestMode.MOCK_HARDWARE

# Set IP address of real spectrum device (for use if TestMode.REAL_HARDWARE is set above)
TEST_DEVICE_IP = "169.254.142.75"
NUM_MODULES_PER_CARD = 2
NUM_CHANNELS_PER_MODULE = 4
NUM_CARDS_IN_STAR_HUB = 2
STAR_HUB_MASTER_CARD_INDEX = 1
mock_device_test_frame_rate_hz = 10.0


if SINGLE_CARD_TEST_MODE == SpectrumTestMode.REAL_HARDWARE and not SPECTRUM_DRIVERS_FOUND:
    raise SpectrumIOError(
        "Cannot run single card tests in REAL_HARDWARE mode because no Spectrum drivers were found."
        "Set SINGLE_CARD_TEST_MODE = SpectrumTestMode.MOCK_HARDWARE in configuration.py."
    )
if STAR_HUB_TEST_MODE == SpectrumTestMode.REAL_HARDWARE and not SPECTRUM_DRIVERS_FOUND:
    raise SpectrumIOError(
        "Cannot run star-hub tests in REAL_HARDWARE mode because no Spectrum drivers were found"
        "Set STAR_HUB_TEST_MODE = SpectrumTestMode.MOCK_HARDWARE in configuration.py."
    )
