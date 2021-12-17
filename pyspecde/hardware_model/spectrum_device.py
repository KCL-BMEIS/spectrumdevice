from abc import ABC

from pyspecde.exceptions import SpectrumDeviceNotConnected
from spectrum_gmbh.regs import (
    M2CMD_CARD_RESET,
    M2CMD_CARD_START,
    SPC_M2CMD,
    M2CMD_CARD_ENABLETRIGGER,
    M2CMD_CARD_STOP,
)

from pyspecde.hardware_model.spectrum_interface import (
    SpectrumDeviceInterface,
    SpectrumIntLengths,
)
from pyspecde.spectrum_api_wrapper import (
    get_spectrum_i32_api_param,
    get_spectrum_i64_api_param,
    set_spectrum_i32_api_param,
    set_spectrum_i64_api_param,
    spectrum_handle_factory,
)


class SpectrumDevice(SpectrumDeviceInterface, ABC):
    def _connect(self, visa_string: str) -> None:
        self._handle = spectrum_handle_factory(visa_string)
        self._connected = True

    def reset(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_CARD_RESET)

    def start_acquisition(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)

    def stop_acquisition(self) -> None:
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_CARD_STOP)  # | M2CMD_CARD_DISABLETRIGGER)

    def set_spectrum_api_param(
        self,
        spectrum_register: int,
        value: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> None:
        if self.connected:
            if length == SpectrumIntLengths.THIRTY_TWO:
                set_spectrum_i32_api_param(self.handle, spectrum_register, value)
            elif length == SpectrumIntLengths.SIXTY_FOUR:
                set_spectrum_i64_api_param(self.handle, spectrum_register, value)
            else:
                raise ValueError("Spectrum integer length not recognised.")
        else:
            raise SpectrumDeviceNotConnected("The device has been disconnected.")

    def get_spectrum_api_param(
        self,
        spectrum_register: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> int:
        if self.connected:
            if length == SpectrumIntLengths.THIRTY_TWO:
                return get_spectrum_i32_api_param(self.handle, spectrum_register)
            elif length == SpectrumIntLengths.SIXTY_FOUR:
                return get_spectrum_i64_api_param(self.handle, spectrum_register)
            else:
                raise ValueError("Spectrum integer length not recognised.")
        else:
            raise SpectrumDeviceNotConnected("The device has been disconnected.")


def create_visa_string_from_ip(ip_address: str, instrument_number: int) -> str:
    return f"TCPIP[0]::{ip_address}::inst{instrument_number}::INSTR"
