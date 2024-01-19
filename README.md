A high-level, object-oriented Python library for controlling Spectrum Instrumentation devices.

`spectrumdevice` can connect to individual cards or 
[StarHubs](https://spectrum-instrumentation.com/en/m4i-star-hub) (e.g. the
[NetBox](https://spectrum-instrumentation.com/en/digitizernetbox)). `spectrumdevice` provides the following classes 
for controlling devices:

| Name                       | Purpose                                                               |
|----------------------------|-----------------------------------------------------------------------|
| `SpectrumDigitiserCard`    | Controlling individual digitiser cards                                |
| `SpectrumDigitiserStarHub` | Controlling digitiser cards aggregated with a StarHub                 |
| `SpectrumAWGCard`          | Controlling individual AWG cards                                      |
| `SpectrumAWGStarHub`       | Controlling AWG cards aggregated with a StarHub (Not yet implemented) |

`spectrumdevice` also includes mock classes for testing software without drivers installed or hardware connected:

| Name                           | Purpose                                                           |
|--------------------------------|-------------------------------------------------------------------|
| `MockSpectrumDigitiserCard`    | Mocking individual digitiser cards                                |
| `MockSpectrumDigitiserStarHub` | Mocking digitiser cards aggregated with a StarHub                 |
| `MockSpectrumAWGCard`          | Mocking individual AWG cards                                      |
| `MockSpectrumAWGStarHub`       | Mocking AWG cards aggregated with a StarHub (Not yet implemented) |

For digitisers, `spectrumdevice` currently only supports 'Standard Single' and 'Multi FIFO' acquisition modes. For AWGs,
'Standard Single' and Standard Single Restart' modes are supported. See the Limitations section for more information. 

* [Examples](https://github.com/KCL-BMEIS/spectrumdevice/tree/main/example_scripts)
* [API reference documentation](https://kcl-bmeis.github.io/spectrumdevice/)
* [PyPI](https://pypi.org/project/spectrumdevice/)

## Requirements
Python 3.9+

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
files taken from the `spcm_examples` directory, provided with Spectrum hardware. The files in this module were written 
by Spectrum GMBH and are included with their permission. The files provide `spectrumdevice` with a low-level Python 
interface to the Spectrum driver and define global constants which are used throughout `spectrumdevice`.

## Limitations
* Currently, `spectrumdevice` only supports Standard Single and Multi FIFO digitiser acquisition modes. See the 
  Spectrum documentation for more information.
* Only Standard Single and Standard Single Restart modes have been implemented for AWGs.
* If timestamping is enabled, timestamps are acquired using Spectrum's 'polling' mode. This seems to add around
  5 to 10 ms of latency to the acquisition.
* Only current digitisers from the [59xx](https://spectrum-instrumentation.com/de/59xx-16-bit-digitizer-125-mss),
[44xx](https://spectrum-instrumentation.com/de/44xx-1416-bit-digitizers-500-mss) and 
[22xx](https://spectrum-instrumentation.com/de/22xx-8-bit-digitizers-5-gss) families are currently supported, and 
`spectrumdevice` has only been tested on 59xx digitisers and 65xx AWGs. However, `spectrumdevice` may work fine on older
devices. If you've tried `spectrumdevice` on an older device, please let us know if it works and raise any issues you
encounter in the issue tracker. It's likely possible to add support with minimal effort.

## Usage
### Connect to devices
Connect to local (PCIe) cards:

```python
from spectrumdevice import SpectrumDigitiserCard, SpectrumAWGCard

digitiser_1 = SpectrumDigitiserCard(device_number=0)
awg_1 = SpectrumAWGCard(device_number=1)
```
Connect to networked cards (you can find a card's IP using the
[Spectrum Control Centre](https://spectrum-instrumentation.com/en/spectrum-control-center) software):

```python
from spectrumdevice import SpectrumDigitiserCard

card_0 = SpectrumDigitiserCard(device_number=0, ip_address="192.168.0.2")
card_1 = SpectrumDigitiserCard(device_number=0, ip_address="192.168.0.3")
```

Connect to a networked StarHub (e.g. a NetBox).

```python
from spectrumdevice import SpectrumDigitiserCard, SpectrumDigitiserStarHub

NUM_CARDS_IN_STAR_HUB = 2
STAR_HUB_MASTER_CARD_INDEX = 1  # The card controlling the clock
HUB_IP_ADDRESS = "192.168.0.2"

# Connect to each card in the hub.
child_cards = []
for n in range(NUM_CARDS_IN_STAR_HUB):
  child_cards.append(SpectrumDigitiserCard(device_number=n, ip_address=HUB_IP_ADDRESS))

# Connect to the hub itself
hub = SpectrumDigitiserStarHub(device_number=0, child_cards=child_cards,
                               master_card_index=STAR_HUB_MASTER_CARD_INDEX)
```
Once connected, a `SpectrumStarHub` object can be configured and used in exactly the same way as a `SpectrumCard` 
object — commands will be sent to the child cards automatically.

### Using Mock Devices
You can use mock devices to test your software without hardware connected or drivers installed. 
After construction, Mock devices have the same interface as real devices. Mock digitisers provide random waveforms 
generated by an internal mock data source. The number of channels and modules in a mock card must be provided on 
construction as shown below. You can match these values to your hardware by inspecting the number of channels and 
modules in a hardware device using the
[Spectrum Control Centre](https://spectrum-instrumentation.com/en/spectrum-control-center) software. The frame rate 
of the mock data source must also be set on construction.

```python
from spectrumdevice import MockSpectrumDigitiserCard, MockSpectrumDigitiserStarHub, MockSpectrumAWGCard
from spectrumdevice.settings import ModelNumber

mock_digitiser = MockSpectrumDigitiserCard(
    device_number=0,
    model=ModelNumber.TYP_M2P5966_X4,
    mock_source_frame_rate_hz=10.0,
    num_modules=2,
    num_channels_per_module=4
)
mock_hub = MockSpectrumDigitiserStarHub(device_number=0, child_cards=[mock_digitiser], master_card_index=0)
mock_awg = MockSpectrumAWGCard(
    device_number=0,
    model=ModelNumber.TYP_M2P6560_X4,
    num_modules=1,
    num_channels_per_module=1
)
```
After construction, mock devices can be used identically to real devices.

### Configuring device settings
`SpectrumDigitiserCard`, `SpectrumDigitiserStarHub` and `SpectrumAWGCard` provide methods for reading and writing device
settings located within on-device registers. Some settings must be set using Enums imported from the `settings` module.
 Others are set using integer values. For example, to put a digitiser card in 'Standard Single' acquisition mode and set
the sample rate to 10 MHz:

```python
from spectrumdevice import SpectrumDigitiserCard
from spectrumdevice.settings import AcquisitionMode

digitiser_card = SpectrumDigitiserCard(device_number=0)
digitiser_card.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
digitiser_card.set_sample_rate_in_hz(10000000)
```
and to print the currently set sample rate:

```python
print(card.sample_rate_in_hz)
```

### Configuring channel settings
The analog channels available to a spectrum device (card or StarHub) can be accessed via the `analog_channels` property.
 This property contains a list of `SpectrumDigitiserChannel` or `SpectrumAWGChannel` objects which provide methods for 
independently configuring each channel. For example, to change the vertical range of channel 2 of a digitiser card to 1V:

```python
digitiser_card.analog_channels[2].set_vertical_range_in_mv(1000)
```
and then print the vertical offset:

```python
print(digitiser_card.analog_channels[2].vertical_offset_in_percent)
```

### Configuring everything at once
You can set multiple settings at once using the `TriggerSettings`, `AcquisitionSettings` and `GenerationSettings` 
dataclasses and the `configure_trigger()`, `configure_acquisition()` and `configure_generation()` methods:

```python
import numpy as np

from spectrumdevice import SpectrumDigitiserCard, SpectrumAWGCard
from spectrumdevice.settings import TriggerSettings, AcquisitionSettings, TriggerSource, ExternalTriggerMode, \
AcquisitionMode, GenerationSettings, GenerationMode, OutputChannelFilter, OutputChannelStopLevelMode
from spectrumdevice.settings.channel import InputImpedance

digitiser_card = SpectrumDigitiserCard(device_number=0)
awg_card = SpectrumAWGCard(device_number=1)

trigger_settings = TriggerSettings(
  trigger_sources=[TriggerSource.SPC_TMASK_EXT0],
  external_trigger_mode=ExternalTriggerMode.SPC_TM_POS,
  external_trigger_level_in_mv=1000,
)
digitiser_card.configure_trigger(trigger_settings)
awg_card.configure_trigger(trigger_settings)

acquisition_settings = AcquisitionSettings(
  acquisition_mode=AcquisitionMode.SPC_REC_FIFO_MULTI,
  sample_rate_in_hz=40000000,
  acquisition_length_in_samples=400,
  pre_trigger_length_in_samples=0,
  timeout_in_ms=1000,
  enabled_channels=[0, 1, 2, 3],
  vertical_ranges_in_mv=[200, 200, 200, 200],
  vertical_offsets_in_percent=[0, 0, 0, 0],
  input_impedances=[InputImpedance.ONE_MEGA_OHM, InputImpedance.ONE_MEGA_OHM, InputImpedance.ONE_MEGA_OHM, InputImpedance.ONE_MEGA_OHM],
  timestamping_enabled=True,
  batch_size=1
)
digitiser_card.configure_acquisition(acquisition_settings)

generation_settings = GenerationSettings(
    generation_mode=GenerationMode.SPC_REP_STD_SINGLERESTART,
    waveform=np.array(np.ones(16), dtype=np.int16),
    sample_rate_in_hz=40000000,
    num_loops=5,
    enabled_channels=[0],
    signal_amplitudes_in_mv=[1000],
    dc_offsets_in_mv=[0],
    output_filters=[OutputChannelFilter.LOW_PASS_70_MHZ],
    stop_level_modes=[OutputChannelStopLevelMode.SPCM_STOPLVL_ZERO],
)
awg_card.configure_generation(generation_settings)
```

### Acquiring waveforms from a digitiser (standard single mode)
To acquire data in standard single mode, place the device into the correct mode using `configure_acquisition()` or `
card.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)` and then execute the acquisition:
```python
measurement = card.execute_standard_single_acquisition()
```
`measurement` is a `Measurement` dataclass containing the waveforms received by each enabled channel and, if 
timestamping was enabled in the `AcquisitionSettings`, the time at which the acquisition was triggered:
```python
waveforms = measurement.waveforms  # A list of 1D numpy arrays
timestamp = measurement.timestamp  # A datetime.datetime object
```

### Acquiring waveforms from a digitiser (FIFO mode)
To acquire data in FIFO mode, place the device into the correct mode using `configure_acquisition()` or `
card.set_acquisition_mode(AcquisitionMode.SPC_REC_FIFO_MULTI)`. You can then also construct your own 
`TransferBuffer` object and provide it to card using the `define_transfer_buffer()` method:

```python
from spectrumdevice.settings.transfer_buffer import (
    BufferDirection,
    BufferType,
    transfer_buffer_factory,
)

size_in_samples = 100
board_memory_offset_bytes = 0
notify_size_in_pages = 10

buffer = transfer_buffer_factory(
  buffer_type=BufferType.SPCM_BUF_DATA,  # must be SPCM_BUF_DATA to transfer samples from digitiser
  direction=BufferDirection.SPCM_DIR_CARDTOPC,  # must be SPCM_DIR_CARDTOPC to transfer samples from digitiser
  size_in_samples=size_in_samples,
  bytes_per_sampe=card.bytes_per_sample,
  board_memory_offset_bytes=board_memory_offset_bytes,
  notify_size_in_pages=notify_size_in_pages
)
  
card.define_transfer_buffer(buffer)
```
this allows you to set your own transfer buffer size and notify size. If you do not call `define_transfer_buffer()` yourself,
then a default transfer buffer will be used, which will have a notify size of 10 pages (40 kB) and will be large
enough to hold 1000 repeat acquisitions without overflowing.

You can then carry out a predefined number of Multi FIFO measurements like this:

```python
NUM_MEASUREMENTS = 2
measurements = card.execute_finite_fifo_acquisition(NUM_MEASUREMENTS)
```
`measurements` will be a list of `Measurement` dataclasses (of length `NUM_MEASUREMENTS`), where each 
`Measurement` object contains the waveforms received by each enabled channel during a measurement.

Alternatively, you can start a Multi FIFO acquisition continuously writing data to a software 'transfer' buffer:

```python
card.execute_continuous_fifo_acquisition()
```
But you'll then need to pull the data out of the transfer buffer at least as fast as the data is being acquired,
manually obtaining the waveforms and timestamp:
```python
measurements_list = []
while True:
    measurements_list.append(Measurement(waveforms=card.get_waveforms(),
                                         timestamp=card.get_timestamp()))
```
Each call to `get_waveforms()` will wait until the next set of waveform data is available. When ready, you'll need 
to stop the acquisition:

```python
card.stop()
```
and execute some logic to exit the `while` loop.

### Generating a signal with an AWG
After configuring your trigger and generation settings as shown above, you can start your card:
```python
awg_card.start()
```
The card is now waiting for a trigger. If the card is in software trigger mode, you can trigger its output manually:
```python
awg_card.force_trigger()
```
Then stop and disconnect when finished:
```python
awg_card.stop()
awg_card.disconnect()
```

### Using the optional Pulse Generator firmware add-on
For both AWGs and Digitisers, Spectrum provide an optional pulse generator feature which can be activated retrospectively.

Each of the card's four multipurpose IO lines (X0, X1, X2 and X3) has a pulse generator. Choose the one you would like 
to use and set it to pulse gen mode. Here we are using X0 (index 0)
```python
from spectrumdevice.settings import IOLineMode

io_line_index = 0
card.io_lines[io_line_index].set_mode(IOLineMode.SPCM_XMODE_PULSEGEN)
```
Then get its pulse generator and configure its trigger and output settings
```python
from spectrumdevice.settings import (
    PulseGeneratorTriggerSettings,
    PulseGeneratorTriggerMode,
    PulseGeneratorTriggerDetectionMode,
    PulseGeneratorMultiplexer1TriggerSource,
    PulseGeneratorMultiplexer2TriggerSource,
    PulseGeneratorOutputSettings
)

pulse_gen = card.io_lines[io_line_index].pulse_generator
pg_trigger_settings = PulseGeneratorTriggerSettings(
    trigger_mode=PulseGeneratorTriggerMode.SPCM_PULSEGEN_MODE_SINGLESHOT,
    trigger_detection_mode=PulseGeneratorTriggerDetectionMode.RISING_EDGE,
    multiplexer_1_source=PulseGeneratorMultiplexer1TriggerSource.SPCM_PULSEGEN_MUX1_SRC_UNUSED,
    multiplexer_1_output_inversion=False,
    multiplexer_2_source=PulseGeneratorMultiplexer2TriggerSource.SPCM_PULSEGEN_MUX2_SRC_SOFTWARE,
    multiplexer_2_output_inversion=False,
)
pulse_gen.configure_trigger(pg_trigger_settings)
pulse_output_settings = PulseGeneratorOutputSettings(
    period_in_seconds=1e-3, duty_cycle=0.5, num_pulses=10, delay_in_seconds=0.0, output_inversion=False
)
pulse_gen.configure_output(pulse_output_settings)
# Enable the pulse generator
pulse_gen.enable()
```
We have set the pulse generator to use a software trigger, so you can manually trigger it to start pulsing:
```python
pulse_gen.force_trigger()

card.stop()
card.disconnect()
```
## Examples
See the `example_scripts` directory.

## API Documentation

See [here](https://kcl-bmeis.github.io/spectrumdevice/) for documentation for the complete API.
