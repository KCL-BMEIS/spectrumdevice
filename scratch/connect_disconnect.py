from pyspecde.devices.factories import spectrum_card_factory
from pyspecde.devices.spectrum_card import _create_visa_string_from_ip

device_ip = "169.254.142.75"
visa_string = _create_visa_string_from_ip(ip_address=device_ip, instrument_number=1)
print(visa_string)
card = spectrum_card_factory(visa_string)
io_modes = card.available_io_modes
print("Channel X0")
for mode in io_modes.X0:
    print(mode.name)
print("Channel X1")
for mode in io_modes.X1:
    print(mode.name)
print("Channel X2")
for mode in io_modes.X2:
    print(mode.name)
print("Channel X3")
for mode in io_modes.X3:
    print(mode.name)
card.disconnect()
