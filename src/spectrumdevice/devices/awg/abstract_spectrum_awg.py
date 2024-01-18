from abc import ABC

from spectrum_gmbh.regs import SPC_CARDMODE, SPC_LOOPS
from spectrumdevice.devices.abstract_device import AbstractSpectrumDevice
from spectrumdevice.devices.awg.awg_interface import SpectrumAWGInterface
from spectrumdevice.settings.device_modes import GenerationMode


class AbstractSpectrumAWG(AbstractSpectrumDevice, SpectrumAWGInterface, ABC):
    @property
    def generation_mode(self) -> GenerationMode:
        """Change the currently enabled card mode. See `GenerationMode` and the Spectrum documentation
        for the available modes."""
        return GenerationMode(self.read_spectrum_device_register(SPC_CARDMODE))

    def set_generation_mode(self, mode: GenerationMode) -> None:
        self.write_to_spectrum_device_register(SPC_CARDMODE, mode.value)

    @property
    def num_loops(self) -> int:
        return self.read_spectrum_device_register(SPC_LOOPS)

    def set_num_loops(self, num_loops: int) -> None:
        self.write_to_spectrum_device_register(SPC_LOOPS, num_loops)
