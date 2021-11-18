from abc import ABC

from third_party.specde.py_header.regs import (
    M2CMD_CARD_START,
    SPC_M2CMD,
    M2CMD_CARD_ENABLETRIGGER,
    M2CMD_CARD_STOP,
    M2CMD_CARD_DISABLETRIGGER,
)

from pyspecde.hardware_model.spectrum_interface import (
    SpectrumDeviceInterface,
    SpectrumIntLengths,
)
from pyspecde.sdk_translation_layer import (
    get_spectrum_i32_api_param,
    get_spectrum_i64_api_param,
    set_spectrum_i32_api_param,
    set_spectrum_i64_api_param,
)


class SpectrumDevice(SpectrumDeviceInterface, ABC):
    def run(self) -> None:
        self.start_dma()
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)

    def stop(self) -> None:
        self.stop_dma()
        self.set_spectrum_api_param(SPC_M2CMD, M2CMD_CARD_STOP | M2CMD_CARD_DISABLETRIGGER)

    def set_spectrum_api_param(
        self,
        spectrum_command: int,
        value: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> None:
        if length == SpectrumIntLengths.THIRTY_TWO:
            set_spectrum_i32_api_param(self.handle, spectrum_command, value)
        elif length == SpectrumIntLengths.SIXTY_FOUR:
            set_spectrum_i64_api_param(self.handle, spectrum_command, value)
        else:
            raise ValueError("Spectrum integer length not recognised.")

    def get_spectrum_api_param(
        self,
        spectrum_command: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> int:
        if length == SpectrumIntLengths.THIRTY_TWO:
            return get_spectrum_i32_api_param(self.handle, spectrum_command)
        elif length == SpectrumIntLengths.SIXTY_FOUR:
            return get_spectrum_i64_api_param(self.handle, spectrum_command)
        else:
            raise ValueError("Spectrum integer length not recognised.")