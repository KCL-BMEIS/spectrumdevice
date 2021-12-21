from abc import ABC

from pyspecde.spectrum_wrapper.exceptions import SpectrumDeviceNotConnected
from spectrum_gmbh.regs import (
    M2CMD_CARD_RESET,
    M2CMD_CARD_START,
    SPC_M2CMD,
    M2CMD_CARD_ENABLETRIGGER,
    M2CMD_CARD_STOP,
)

from pyspecde.devices.spectrum_interface import (
    SpectrumDeviceInterface,
)
from pyspecde.settings import SpectrumRegisterLength
from pyspecde.spectrum_wrapper import (
    get_spectrum_i32_api_param,
    get_spectrum_i64_api_param,
    set_spectrum_i32_api_param,
    set_spectrum_i64_api_param,
    spectrum_handle_factory,
)


class SpectrumDevice(SpectrumDeviceInterface, ABC):
    """Abstract superclass which implements methods common to all Spectrum digitizer devices. Instances of this class
    cannot be constructed directly. Instead, construct instances of the concrete classes SpectrumCard, SpectrumStarHub,
    MockSpectrumCard or MockSpectrumStarHub, which inherit the methods defined here. Note that the mock devices override
    several of the methods defined here."""

    def _connect(self, visa_string: str) -> None:
        self._handle = spectrum_handle_factory(visa_string)
        self._connected = True

    def reset(self) -> None:
        """Perform a software and hardware reset.

        All settings are set to hardware default values. The data in the board’s on-board memory will be no longer
        valid. Any output signals like trigger or clock output will be disabled."""
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_RESET)

    def start_acquisition(self) -> None:
        """Start acquiring data.

        In Standard Single mode (SPC_REC_STD_SINGLE), this will need to be called once for each acquisition. In-between
        calls, waveforms must be manually transferred from the device to a TransferBuffer using start_transfer(). The
        TransferBuffer need not be defined until after start_acquisition is called.

        In Multi FIFO mode (SPC_REC_FIFO_MULTI), it needs to be called only once, immediately followed by a call to
        start_transfer(). Frames will the be continuously streamed to the TransferBuffer, which must have already been
        defined.
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)

    def stop_acquisition(self) -> None:
        """Stop acquiring data when in FIFO mode.

        Stop the continuous acquisition of waveform data that occurs after calling start_acquisition() in FIFO mode
        (SPC_REC_FIFO_MULTI). Does not need to be called in Standard Single mode (SPC_REC_STD_SINGLE).
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_STOP)

    def write_to_spectrum_device_register(
        self,
        spectrum_register: int,
        value: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> None:
        """Set the value of a register on the Spectrum digitizer.

        This method is used internally by SpectrumDevice and it's subclasses to configure a hardware device, but can
        also used to set the value of registers that are not implemented in SpectrumDevice and it's subclasses.

        Args:
            spectrum_register (int): Identifier of the register to set. This should be a global constant imported from
                regs.py in the spectrum_gmbh package.
            value (int): Value to write to the register. This should be a global constant imported from
                regs.py in the spectrum_gmbh package.
            length (SpectrumRegisterLength): An SpectrumRegisterLength object specifying the length of the register
                to set, in bits.
        """
        if self.connected:
            if length == SpectrumRegisterLength.THIRTY_TWO:
                set_spectrum_i32_api_param(self._handle, spectrum_register, value)
            elif length == SpectrumRegisterLength.SIXTY_FOUR:
                set_spectrum_i64_api_param(self._handle, spectrum_register, value)
            else:
                raise ValueError("Spectrum integer length not recognised.")
        else:
            raise SpectrumDeviceNotConnected("The device has been disconnected.")

    def read_spectrum_device_register(
        self,
        spectrum_register: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> int:
        """Get the value of a register on the Spectrum digitizer.

        This method is used internally by SpectrumDevice and it's subclasses to read the configration of a hardware
        device, but can be also used to get the value of registers that are not implemented in
        SpectrumDevice and it's subclasses.

        Args:
            spectrum_register (int): Identifier of the register to set. This should be a global constant imported from
                spectrum_gmbh.regs.
            length (SpectrumRegisterLength): An SpectrumRegisterLength object specifying the length of the register to
                set, in bits.

        Returns:
            value (int): Value of the register. This can be matched to a global constant imported from
                spectrum_gmbh.regs, usually using one of the Enums defined in the settings module.
        """
        if self.connected:
            if length == SpectrumRegisterLength.THIRTY_TWO:
                return get_spectrum_i32_api_param(self._handle, spectrum_register)
            elif length == SpectrumRegisterLength.SIXTY_FOUR:
                return get_spectrum_i64_api_param(self._handle, spectrum_register)
            else:
                raise ValueError("Spectrum integer length not recognised.")
        else:
            raise SpectrumDeviceNotConnected("The device has been disconnected.")

    def __repr__(self) -> str:
        return str(self)
