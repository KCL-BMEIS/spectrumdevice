from pyspecde.hardware_model.spectrum_card import spectrum_card_factory
from pyspecde.hardware_model.spectrum_star_hub import create_visa_string_from_ip
from third_party.specde.py_header.regs import SPC_TRIG_AVAILORMASK

device_ip = "169.254.142.75"
visa_string = create_visa_string_from_ip(ip_address=device_ip, instrument_number=1)
print(visa_string)
card = spectrum_card_factory(visa_string)
print(card.get_spectrum_api_param(SPC_TRIG_AVAILORMASK))
card.disconnect()
