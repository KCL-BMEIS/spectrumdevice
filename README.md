# spectrumdevice
A high-level, object-oriented Python API for controlling Spectrum Instruments digitisers.

Spectrum digitisers can be connected individually or grouped together using a
[StarHub](https://spectrum-instrumentation.com/en/m4i-star-hub) (e.g. the
[NetBox](https://spectrum-instrumentation.com/en/digitizernetbox)). `spectrumdevice` provides classes 
`SpectrumCard` and `SpectrumStarHub` for controlling and receiving data from individual digitisers and StarHubs 
respectively.

`spectrumdevice` currently supports 'Standard Single' and 'Multi FIFO' acquisition modes. See the Limitations section for 
more information.

* [Documentation](https://kcl-bmeis.github.io/spectrumdevice/)
* [Source on GitHub](https://github.com/KCL-BMEIS/spectrumdevice/)

## Requirements
`spectrumdevice` works with hardware on Windows and Linux. Spectrum do not currently provide a driver for MacOS, but 
`spectrumdevice` provides mock classes for development and testing without hardware, which work on MacOS.

To work with hardware, `spectrumdevice` requires that you have installed the
[Spectrum driver](https://spectrum-instrumentation.com/en/drivers-and-examples-overview) for your platform.
This should be located at `c:\windows\system32\spcm_win64.dll` (or `spcm_win32.dll` on a 32-bit system) on
on Windows, or in `libspcm_linux.so`on Linux. If no driver is present `spectrumdevice` can still run in mock mode.

## Installation and dependencies
Clone the repository and from within the top level directory, `pip install .`

`spectrumdevice` itself depends on NumPy, and its example scripts make use of `matplotlib`. `spectrumdevice` includes 
a module called `spectrum_gmbh` containing a few files taken from the `spcm_examples` directory which is provided with 
Spectrum hardware. The files in this module were written by Spectrum GMBH and are included with their permission. 
They provide `spectrumdevice` with a low-level Python interface to the DLL and define global constants which are used 
throughout `spectrumdevice`.

## Usage
### Connect to devices
Connect to local (PCIe) cards:

```python
from spectrumdevice import SpectrumCard

card_0 = SpectrumCard(device_number=0)
card_1 = SpectrumCard(device_number=1)
```
Connect to networked cards (you can find a card's IP using the
[Spectrum Control Centre](https://spectrum-instrumentation.com/en/spectrum-control-center) software):

```python
from spectrumdevice import SpectrumCard

card_0 = SpectrumCard(device_number=0, ip_address="192.168.0.2")
card_1 = SpectrumCard(device_number=1, ip_address="192.168.0.3")
```

Connect to a networked StarHub (e.g. a NetBox).

```python
from spectrumdevice import SpectrumCard, SpectrumStarHub

NUM_CARDS_IN_STAR_HUB = 2
STAR_HUB_MASTER_CARD_INDEX = 1  # The card controlling the clock
HUB_IP_ADDRESS = "192.168.0.2"

# Connect to each card in the hub.
child_cards = []
for n in range(NUM_CARDS_IN_STAR_HUB):
  child_cards.append(SpectrumCard(device_number=n, ip_address=HUB_IP_ADDRESS))

# Connect to the hub itself
hub = SpectrumStarHub(device_number=0, child_cards=child_cards,
                      master_card_index=STAR_HUB_MASTER_CARD_INDEX)
```
Once connected, `SpectrumStarHub` object can be configured and used in exactly the same way as a `SpectrumCard` 
object - commands will be sent to the child cards automatically.

### Using Mock Devices
You can test your software without hardware connected or drivers installed using mock devices. After construction, Mock 
devices have the same interface as real devices, and will provide random waveforms using an internal mock waveform 
source. Mock devices require a few more input arguments to be constructed that real hardware devices:

```python
from spectrumdevice import MockSpectrumCard, MockSpectrumStarHub

mock_card = MockSpectrumCard(device_number=0, mock_source_frame_rate_hz=10.0, num_modules=2, num_channels_per_module=4)
mock_hub = MockSpectrumStarHub(device_number=0, child_cards=[mock_card], master_card_index=0)
```
After construction, `MockSpectrumCard` and `MockSpectrumStarHub` classes can be used identically to `SpectrumCard` 
and `SpectrumStarHub` objects.

### Configuring device settings
Spectrum Instrument's own low-level Python API requires that users configure a device by writing values to on-device 
registers. The integer addresses of the registers can be imported from `regs.py` (part of Spectrum 
Instrumentation's own `spcm_examples` directory and included in `spectrumdevice`) along with the values to write for each
valid setting. Values can also be read from the on-device registers.

In `spectrumdevice`, the classes `SpectrumCard` and `SpectrumStarHub` provide methods with meaningful names for 
reading and writing to the registers on a device. The valid values from `regs.py` are wrapped in Python Enums. The 
names of the items of the Enums match the names given in `regs.py` and the Spectrum Instrumentation documentation.

For example, to put a card in 'Standard Single' acquisition mode and set the sample rate to 10 MHz:

```python
from spectrumdevice import SpectrumCard
from spectrumdevice.settings import AcquisitionMode

card = SpectrumCard(device_number=0)
card.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
```
and to print the currently set sample rate:

```python
print(card.sample_rate_in_hz)
```

### Configuring channel settings
The channels available to a spectrum device (card or StarHub) can be accessed via the `channels` property. This 
property contains a list of `SpectrumChannel` objects which provide methods to the configuration of each channel 
independently. For example, to change the vertical range of channel 2 of a card to 1V:

```python
card.channels[2].set_vertical_range_in_mv(1000)
```

### Configuring everything at once
You can set multiple settings at once using the `TriggerSettings` and `AcquisitionSettings` dataclasses and the 
`configure_trigger()` and `configure_acquisition()` methods:

```python
from spectrumdevice.settings import TriggerSettings, AcquisitionSettings, TriggerSource, ExternalTriggerMode,
  AcquisitionMode

trigger_settings = TriggerSettings(
  trigger_sources=[TriggerSource.SPC_TMASK_EXT0],
  external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
  external_trigger_level_in_mv=1000,
)

acquisition_settings = AcquisitionSettings(
  acquisition_mode=AcquisitionMode.SPC_REC_FIFO_MULTI,
  sample_rate_in_hz=40000000,
  acquisition_length_in_samples=400,
  pre_trigger_length_in_samples=0,
  timeout_in_ms=1000,
  enabled_channels=[0, 1, 2, 3],
  vertical_ranges_in_mv=[200, 200, 200, 200],
  vertical_offsets_in_percent=[0, 0, 0, 0],
)

card.configure_trigger(trigger_settings)
card.configure_acquisition(acquisition_settings)
```

### Acquiring waveforms (standard single mode)
To acquire data in standard single mode, place the device into the correct mode using `configure_acquisition()` or `
card.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)` and then execute the acquisition:
```python
waveforms = card.execute_standard_single_acquisition()
```
`waveforms` (a list of 1D NumPy arrays) will contain the waveforms received by each enabled channel.

### Acquiring waveforms (multi FIFO mode)
To acquire data in standard single mode, place the device into the correct mode using `configure_acquisition()` or `
card.set_acquisition_mode(AcquisitionMode.SPC_REC_FIFO_MULTI)`.

You can then carry out a predefined number of Multi FIFO measurements like this:
```python
NUM_MEASUREMENTS = 2
measurements = card.execute_finite_multi_fifo_acquisition(NUM_MEASUREMENTS)
```
`measurements` (a list of lists of 1D NumPy arrays) will contain `NUM_MEASUREMENTS` lists of waveforms, where each 
list of waveforms contains the waveforms received by each enabled channel during a measurement.

Alternatively, you can set a Multi FIFO acquisition running continuously like this:
```python
card.execute_continuous_multi_fifo_acquisition()
```
But you'll then need to pull the data out of the transfer buffer at least as fast as the data is being acquired:
```python
measurements = []
while acquiring:
    measurements.append(card.get_waveforms())
```
Each call to `get_waveforms()` will wait until the next set of waveform data is available. When ready, you'll need 
to stop the acquisition:
```python
card.stop_acquisition()
```

## Examples
See the `example_scripts` directory.

## Limitations
* Currently, `spectrumdevice` only supports Standard Single and Multi FIFO acquisition modes. See the 
  Spectrum documentation for more information.
* When defining a transfer buffer - the software buffer into which samples are transferred from a hardware device - 
  the notify size is automatically set equal to the buffer length. This works fine for most situations. See the 
  Spectrum documentation for more information.

## API Documentation

See [here](https://kcl-bmeis.github.io/spectrumdevice/) for documentation for the complete API.
