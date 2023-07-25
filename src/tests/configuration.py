from enum import Enum

from spectrumdevice.settings import TriggerSource
from spectrumdevice.spectrum_wrapper import SPECTRUM_DRIVERS_FOUND
from spectrumdevice.exceptions import SpectrumIOError


class SpectrumTestMode(Enum):
    MOCK_HARDWARE = 0
    REAL_HARDWARE = 1


# Set to TestMode.MOCK_HARDWARE for software-only testing, even if Spectrum drivers are found on the system
# Set to TestMode.REAL_HARDWARE to run tests on a real hardware device as configured below.
SINGLE_CARD_TEST_MODE = SpectrumTestMode.MOCK_HARDWARE
STAR_HUB_TEST_MODE = SpectrumTestMode.MOCK_HARDWARE

# Set IP address of real spectrum device (for use if TestMode.REAL_HARDWARE is set above). Set to None to run tests on
# a local (PCIe) card.
TEST_DEVICE_IP = "169.254.45.181"
# Set the device number to connect to for real hardware tests. If using a star hub (e.g. netbox), this should be the
# STAR_HUB_MASTER_CARD_INDEX. If you only have a single, local (PCIe) card, set to 0.
TEST_DEVICE_NUMBER = 1

# Configure the card. These values are used to set up Mock devices as well as to check the configuration of real
# hardware devices, so should match your real hardware if SpectrumTestMode.REAL_HARDWARE is being used.
NUM_MODULES_PER_CARD = 2
NUM_CHANNELS_PER_MODULE = 4
NUM_CARDS_IN_STAR_HUB = 2
STAR_HUB_MASTER_CARD_INDEX = 1

# Number of samples to acquire per channel during unit testing (on both mock and real devices)
ACQUISITION_LENGTH = 400

# Rate at which mock frames (sets of waveforms) will be generated in SpectrumTestMode.MOCK_HARDWARE
MOCK_DEVICE_TEST_FRAME_RATE_HZ = 10.0

# Trigger source to use for integration tests. Has no effect in SpectrumTestMode.MOCK_HARDWARE
INTEGRATION_TEST_TRIGGER_SOURCE = TriggerSource.SPC_TMASK_EXT0


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
