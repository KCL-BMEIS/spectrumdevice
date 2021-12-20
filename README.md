# pyspecde
A high-level, object-oriented Python API for controlling Spectrum Instruments digitisers.

Spectrum digitisers can be connected individually or grouped together using a
[StarHub](https://spectrum-instrumentation.com/en/m4i-star-hub) (e.g. the
[NetBox](https://spectrum-instrumentation.com/en/digitizernetbox)). `pyspecde` provides classes 
`SpectrumCard` and `SpectrumDevice` for controlling and receiving data from individual digitisers and StarHubs 
respectively.

`pysepcde` currently supports 'Standard Single' and 'Multi FIFO' acquisition modes. See the Limitations section for 
more information.

## Requirements
`pyspecde` works with hardware on Windows and Linux. Spectrum do not currently provide a driver for MacOS, but 
`pyspede` provides mock classes for development and testing without hardware, which work on MacOS.

To work with hardware, `pyspecde` requires that you have installed the
[Spectrum driver](https://spectrum-instrumentation.com/en/drivers-and-examples-overview) for your platform.
This should be located at `c:\windows\system32\spcm_win64.dll` (or `spcm_win32.dll` on a 32-bit system) on
on Windows, or in `libspcm_linux.so`on Linux. If no driver is found,  `pyspecde` will run in mock mode.

## Installation and dependencies
Clone the repository and from within the top level directory, `pip install .` Or install from PyPI or conda-forge with 
`pip install pyspecde` or `conda install pyspecde` respectively.

`pysepcde` itself depends on NumPy, and its example scripts make use of `matplotlib`. `pyspecde` includes 
a module called `spectrum_gmbh` containing a few files taken from the `spcm_examples` directory which is provided with 
Spectrum hardware. The files in this module were written by Spectrum GMBH and are included with their permission. 
They provide `pysepcde` with a low-level Python interface to the DLL and define global constants which are used 
throughout `pyspecde`.

## Usage
### Connect to devices
Connect to local (PCIe) cards:
```python
from pyspecde.hardware_model.spectrum_card import SpectrumCard

card_0 = SpectrumCard(device_number=0)
card_1 = SpectrumCard(device_number=1)
```
Connect to networked cards (you can find a card's IP using the
[Spectrum Control Centre](https://spectrum-instrumentation.com/en/spectrum-control-center) software):
```python
from pyspecde.hardware_model.spectrum_card import SpectrumCard

card_0 = SpectrumCard(device_number=0, ip_address="192.168.0.2")
card_1 = SpectrumCard(device_number=1, ip_address="192.168.0.2")
```

Connect to a networked StarHub (e.g. a NetBox).
```python
from pyspecde.hardware_model.spectrum_star_hub import SpectrumStarHub
 

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

### Configuring acquisitions
Spectrum Instrument's own low-level Python API requires that users configure a device by writing values to on-device 
registers. The integer addresses of the registers can be imported from `regs.py` (part of Spectrum 
Instrumentation's own `spcm_examples` directory and included in `pyspecde`) along with the values to write for each
valid setting. Values can also be read from the on-device registers.

In `pyspecde`, the classes `SpectrumCard` and `SpectrumStarHub` provide methods with meaningful names for 
reading and writing to the registers on a device. The valid values from `regs.py` are wrapped in Python Enums. The 
names of the items of the Enums match the names given in `regs.py` and the Spectrum Instrumentation documentation.

For example, to put a card in 'Standard Single' acquisition mode and set the sample rate to 10 MHz:
```python
from pyspecde.hardware_model.spectrum_card import SpectrumCard
from pyspecde.spectrum_api_wrapper import AcquisitionMode

card = SpectrumCard(device_number=0)
card.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)
```
and to print the currently set sample rate:
```python
print(card.sample_rate_hz)
```

### Configuring channels
The channels available to a spectrum device (card or StarHub) can be accessed via the `channels` property. This 
property contains a list of `SpectrumChannel` objects which provide methods to the configuration of each channel 
independently. For example, to change the vertical range of channel 2 of a card to 1V:
```python
card.channels[2].set_vertical_range_mv(1000)
```

### Acquiring waveforms (standard single mode)
To acquire data in standard single mode, after calling
```python
card.set_acquisition_mode(AcquisitionMode.SPC_REC_STD_SINGLE)`
```
and configuring your other acquisition and channel settings (length, trigger setup, enabled channels, timeout, 
channel ranges etc.), you need to start the acquisition and wait for it to 
complete:
```python
card.start_acquisition()
card.wait_for_acquisition_to_complete()
```
To retrieve the acquired waveforms, you need to create a transfer buffer into which your acquired samples will be 
written:
```python
card.define_transfer_buffer()
```
and then start the transfer of samples from the on-device buffer to the transfer buffer, and wait for it to complete:
```python
card.start_transfer()
card.wait_for_transfer_to_complete()
```
Once the transfer is complete, you can obtain your waveforms as a list of 1D NumPy arrays:
```python
waveforms = card.get_waveforms()
```

### Acquiring waveforms (multi FIFO mode)
Put your device in Multi-FIFO mode using:
```python
card.set_acquisition_mode(AcquisitionMode.SPC_REC_FIFO_MULTI)`
```
In multi FIFO mode, samples are streamed from the on-device buffer to the software buffer during the acquisition. 
This means the transfer buffer must be defined before the acquisition begins, and the transfer started immediately:
```python
card.define_transfer_buffer()
card.start_acquisition()
card.start_transfer()
```
You then need to pull the data out of the transfer buffer at least as fast as the data is being acquired:
```python
acquisitions = []
while acquiring:
    acquisitions.append(card.get_waveforms())
```
Each call to `get_waveforms()` will wait until the next set of waveform data is available.

To stop the acquisitions and therefor the transfer of data into the transfer buffer:
```python
card.stop_acquisition()
```
