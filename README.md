# spectrumdevice
A high-level, object-oriented Python library for controlling Spectrum Instrumentation digitisers.

`spectrumdevice` can connect to individual digitisers or 
[StarHubs](https://spectrum-instrumentation.com/en/m4i-star-hub) (e.g. the
[NetBox](https://spectrum-instrumentation.com/en/digitizernetbox)). `spectrumdevice` provides two classes 
`SpectrumCard` and `SpectrumStarHub` for controlling and receiving data from individual digitisers and StarHubs 
respectively.

`spectrumdevice` currently supports 'Standard Single' and 'Multi FIFO' acquisition modes. See the Limitations section for 
more information.

`spectrumdevice` includes mock classes for testing software without drivers installed or hardware connected.

* [Examples](https://github.com/KCL-BMEIS/spectrumdevice/tree/main/example_scripts)
* [API reference documentation](https://kcl-bmeis.github.io/spectrumdevice/)
* [PyPI](https://pypi.org/project/spectrumdevice/)

## Requirements
`spectrumdevice` works with hardware on Windows and Linux. Spectrum do not currently provide a hardware driver for 
macOS, but `spectrumdevice` provides mock classes for development and testing without hardware, which work on macOS.

To work with hardware, `spectrumdevice` requires that you have installed the
[Spectrum driver](https://spectrum-instrumentation.com/en/drivers-and-examples-overview) for your platform.
On Windows, this should be located at `c:\windows\system32\spcm_win64.dll` (or `spcm_win32.dll` on a 32-bit system). On
Linux, it will be called `libspcm_linux.so`. If no driver is present `spectrumdevice` can still run in mock mode.

## Installation and dependencies
To install the latest release using `pip`:
```
pip install spectrumdevice
```
To install the latest release using `conda`:
```
conda install -c conda-forge spectrumdevice
```

To install the development version:
```
pip install https://github.com/KCL-BMEIS/spectrumdevice/tarball/main.
```

`spectrumdevice` depends only on NumPy. `spectrumdevice` includes a module called `spectrum_gmbh` containing a few 
files taken from the `spcm_examples` directory, provided with Spectrum hardware. The files in this module were written by Spectrum GMBH and are included with their permission. The files provide `spectrumdevice` with a low-level Python interface to the Spectrum driver and define global constants which are used throughout `spectrumdevice`.

## Limitations
* Currently, `spectrumdevice` only supports Standard Single and Multi FIFO acquisition modes. See the 
  Spectrum documentation for more information.
* When defining a transfer buffer - the software buffer into which samples are transferred from a hardware device - 
  the notify-size is automatically set equal to the buffer length. This works fine for most situations. See the 
  Spectrum documentation for more information.
* Only current digitisers from the [59xx](https://spectrum-instrumentation.com/de/59xx-16-bit-digitizer-125-mss),
[44xx](https://spectrum-instrumentation.com/de/44xx-1416-bit-digitizers-500-mss) and 
[22xx](https://spectrum-instrumentation.com/de/22xx-8-bit-digitizers-5-gss) families are currently supported, and 
`spectrumdevice` has only been tested on 59xx devices. However, `spectrumdevice` may work fine on older devices. If 
you've tried `spectrumdevice` on an older device, please let us know if it works and raise any issues you encounter in
the issue tracker. It's likely possible to add support with minimal effort.

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
Once connected, a `SpectrumStarHub` object can be configured and used in exactly the same way as a `SpectrumCard` 
object — commands will be sent to the child cards automatically.

### Using Mock Devices
You can use mock devices to test your software without hardware connected or drivers installed. 
After construction, Mock devices have the same interface as real devices. They provide random waveforms generated 
by an internal mock data source. The number of channels and modules in a mock card must be provided on 
construction as shown below. You can match these values to your hardware by inspecting the number of channels and 
modules in a hardware device using the
[Spectrum Control Centre](https://spectrum-instrumentation.com/en/spectrum-control-center) software. The frame rate 
of the mock data source must also be set on construction.

```python
from spectrumdevice import MockSpectrumCard, MockSpectrumStarHub
from spectrumdevice.settings import CardType

mock_card = MockSpectrumCard(device_number=0, card_type=CardType.TYP_M2P5966_X4, mock_source_frame_rate_hz=10.0, 
                             num_modules=2, num_channels_per_module=4)
mock_hub = MockSpectrumStarHub(device_number=0, child_cards=[mock_card], master_card_index=0)
```
After construction, `MockSpectrumCard` and `MockSpectrumStarHub` can be used identically to `SpectrumCard` 
and `SpectrumStarHub`.

### Configuring device settings
`SpectrumCard` and `SpectrumStarHub` provide methods for reading and writing device settings located within 
on-device registers. Some settings must be set using Enums imported from the `settings` module. Others are set using 
integers. For example, to put a card in 'Standard Single' acquisition mode and set the sample rate to 10 MHz:

```python
from spectrumdevice import SpectrumCard
from spectrumdevice.settings import AcquisitionMode

card = SpectrumCard(device_number=0)
card.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
card.set_sample_rate_in_hz(10000000)
```
and to print the currently set sample rate:

```python
print(card.sample_rate_in_hz)
```

### Configuring channel settings
The channels available to a spectrum device (card or StarHub) can be accessed via the `channels` property. This 
property contains a list of `SpectrumChannel` objects which provide methods for independently configuring each channel. 
For example, to change the vertical range of channel 2 of a card to 1V:

```python
card.channels[2].set_vertical_range_in_mv(1000)
```
and then print the vertical offset:
```python
print(card.channels[2].vertical_offset_in_percent)
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
To acquire data in multi FIFO mode, place the device into the correct mode using `configure_acquisition()` or `
card.set_acquisition_mode(AcquisitionMode.SPC_REC_FIFO_MULTI)`.

You can then carry out a predefined number of Multi FIFO measurements like this:
```python
NUM_MEASUREMENTS = 2
measurements = card.execute_finite_multi_fifo_acquisition(NUM_MEASUREMENTS)
```
`measurements` (a list of lists of 1D NumPy arrays) will contain `NUM_MEASUREMENTS` lists of waveforms, where each 
list of waveforms contains the waveforms received by each enabled channel during a measurement.

Alternatively, you can start a Multi FIFO acquisition continuously writing data to a software 'transfer' buffer:
```python
card.execute_continuous_multi_fifo_acquisition()
```
But you'll then need to pull the data out of the transfer buffer at least as fast as the data is being acquired:
```python
measurements = []
while True:
    measurements.append(card.get_waveforms())
```
Each call to `get_waveforms()` will wait until the next set of waveform data is available. When ready, you'll need 
to stop the acquisition:
```python
card.stop_acquisition()
```
and execute some logic to exit the `while` loop.
## Examples
See the `example_scripts` directory.

## API Documentation

See [here](https://kcl-bmeis.github.io/spectrumdevice/) for documentation for the complete API.
