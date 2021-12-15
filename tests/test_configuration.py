from enum import Enum

from pyspecde.hardware_model.spectrum_card import SpectrumCardConfig
from pyspecde.hardware_model.spectrum_star_hub import SpectrumStarHubConfig
from pyspecde.spectrum_api_wrapper import SPECTRUM_DRIVERS_FOUND
from pyspecde.exceptions import SpectrumIOError


class SpectrumTestMode(Enum):
    MOCK_HARDWARE = 0
    REAL_HARDWARE = 1


# Set to TestMode.MOCK_HARDWARE for software-only testing, even if Spectrum drivers are found on the system
# Set to TestMode.REAL_HARDWARE to run tests on a real hardware device as configured below if Spectrum drivers are
# installed. If drivers are not installed, mock hardware will be used.
SINGLE_CARD_TEST_MODE = SpectrumTestMode.MOCK_HARDWARE
STAR_HUB_TEST_MODE = SpectrumTestMode.MOCK_HARDWARE

# Set IP address of real spectrum device (for use if TestMode.REAL_HARDWARE is set above)
REAL_DEVICE_IP = "169.254.142.75"

# Configure a spectrum card for mock and real tests. For real tests, settings must match the real hardware.
TEST_SPECTRUM_CARD_CONFIG = SpectrumCardConfig(
    REAL_DEVICE_IP, visa_device_num=1, num_modules=2, num_channels_per_module=4
)

# Configure a spectrum Star-Hub (e.g. a Netbox) containing several cards for mock or real tests.
# For real tests, settings must match the real hardware.

child_card_configs = [
    SpectrumCardConfig(REAL_DEVICE_IP, visa_device_num=0, num_modules=2, num_channels_per_module=4),
    SpectrumCardConfig(REAL_DEVICE_IP, visa_device_num=1, num_modules=2, num_channels_per_module=4),
]

TEST_SPECTRUM_STAR_HUB_CONFIG = SpectrumStarHubConfig(
    REAL_DEVICE_IP, card_configs=child_card_configs, master_card_index=1
)

if SINGLE_CARD_TEST_MODE == SpectrumTestMode.REAL_HARDWARE and not SPECTRUM_DRIVERS_FOUND:
    raise SpectrumIOError(
        "Cannot run single card tests in REAL_HARDWARE mode because no Spectrum drivers were found."
        "Set SINGLE_CARD_TEST_MODE = SpectrumTestMode.MOCK_HARDWARE in test_configuration.py."
    )
if STAR_HUB_TEST_MODE == SpectrumTestMode.REAL_HARDWARE and not SPECTRUM_DRIVERS_FOUND:
    raise SpectrumIOError(
        "Cannot run star-hub tests in REAL_HARDWARE mode because no Spectrum drivers were found"
        "Set STAR_HUB_TEST_MODE = SpectrumTestMode.MOCK_HARDWARE in test_configuration.py."
    )
TEST_FRAME_RATE_HZ = 10.0
