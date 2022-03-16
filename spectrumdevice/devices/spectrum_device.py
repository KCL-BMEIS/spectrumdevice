"""Defines a part-implemented abstract superclass for all Spectrum digitiser devices."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from abc import ABC
from typing import List

from spectrum_gmbh.regs import (
    M2CMD_CARD_RESET,
    M2CMD_CARD_START,
    SPC_M2CMD,
    M2CMD_CARD_ENABLETRIGGER,
    M2CMD_CARD_STOP,
    M2CMD_CARD_WRITESETUP,
)
from spectrumdevice.devices.measurement import Measurement
from spectrumdevice.devices.spectrum_interface import (
    SpectrumDeviceInterface,
)
from spectrumdevice.exceptions import (
    SpectrumDeviceNotConnected,
    SpectrumWrongAcquisitionMode,
    SpectrumDriversNotFound,
)
from spectrumdevice.settings import AcquisitionMode, TriggerSettings, AcquisitionSettings
from spectrumdevice.settings import SpectrumRegisterLength
from spectrumdevice.settings.triggering import EXTERNAL_TRIGGER_SOURCES
from spectrumdevice.spectrum_wrapper import (
    get_spectrum_i32_api_param,
    get_spectrum_i64_api_param,
    set_spectrum_i32_api_param,
    set_spectrum_i64_api_param,
    spectrum_handle_factory,
    SPECTRUM_DRIVERS_FOUND,
)


class SpectrumDevice(SpectrumDeviceInterface, ABC):
    """Abstract superclass which implements methods common to all Spectrum digitiser devices. Instances of this class
    cannot be constructed directly. Instead, construct instances of the concrete classes `SpectrumCard`,
    `SpectrumStarHub`, `MockSpectrumCard` or `MockSpectrumStarHub`, which inherit the methods defined here. Note that
    the mock devices override several of the methods defined here."""

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
        calls, waveforms must be manually transferred from the device to a `TransferBuffer` using `start_transfer()`.
        The `TransferBuffer` need not be defined until after `start_acquisition` is called.

        In Multi FIFO mode (SPC_REC_FIFO_MULTI), it needs to be called only once, immediately followed by a call to
        `start_transfer()`. Frames will then be continuously streamed to the `TransferBuffer`, which must have already
        been defined.
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER)

    def stop_acquisition(self) -> None:
        """Stop acquiring data when in FIFO mode.

        Stop the continuous acquisition of waveform data that occurs after calling `start_acquisition()` in FIFO mode
        (SPC_REC_FIFO_MULTI). Does not need to be called in Standard Single mode (SPC_REC_STD_SINGLE).
        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_STOP)

    def configure_acquisition(self, settings: AcquisitionSettings) -> None:
        """Apply all the settings contained in an `AcquisitionSettings` dataclass to the device.

        Args:
            settings (`AcquisitionSettings`): An `AcquisitionSettings` dataclass containing the setting values to apply.
        """
        self._acquisition_mode = settings.acquisition_mode
        self.set_acquisition_mode(settings.acquisition_mode)
        self.set_sample_rate_in_hz(settings.sample_rate_in_hz)
        self.set_acquisition_length_in_samples(settings.acquisition_length_in_samples)
        self.set_post_trigger_length_in_samples(
            settings.acquisition_length_in_samples - settings.pre_trigger_length_in_samples
        )
        self.set_timeout_in_ms(settings.timeout_in_ms)
        self.set_enabled_channels(settings.enabled_channels)
        for channel, v_range, v_offset in zip(
            self.channels, settings.vertical_ranges_in_mv, settings.vertical_offsets_in_percent
        ):
            channel.set_vertical_range_in_mv(v_range)
            channel.set_vertical_offset_in_percent(v_offset)

        # Write the configuration to the card
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_WRITESETUP)

        if settings.timestamping_enabled:
            self.enable_timestamping()

    def configure_trigger(self, settings: TriggerSettings) -> None:
        """Apply all the trigger settings contained in a `TriggerSettings` dataclass to the device.

        Args:
            settings (`TriggerSettings`): A `TriggerSettings` dataclass containing the setting values to apply."""
        self.set_trigger_sources(settings.trigger_sources)
        if len(set(self.trigger_sources) & set(EXTERNAL_TRIGGER_SOURCES)) > 0:
            if settings.external_trigger_mode is not None:
                self.set_external_trigger_mode(settings.external_trigger_mode)
            if settings.external_trigger_level_in_mv is not None:
                self.set_external_trigger_level_in_mv(settings.external_trigger_level_in_mv)
            if settings.external_trigger_pulse_width_in_samples is not None:
                self.set_external_trigger_pulse_width_in_samples(settings.external_trigger_pulse_width_in_samples)

        # Write the configuration to the card
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_WRITESETUP)

    def execute_standard_single_acquisition(self) -> Measurement:
        """Carry out an single measurement in standard single mode and return the acquired waveforms.

        This method automatically carries out a standard single mode acquisition, including handling the creation
        of a `TransferBuffer` and the retrieval of the acquired waveforms. After being called, it will wait until a
        trigger event is received before carrying out the acquisition and then transferring and returning the acquired
        waveforms. The device must be configured in SPC_REC_STD_SINGLE acquisition mode.

        Returns:
            measurement (Measurement): A Measurement object. The `.waveforms` attribute of `measurement` will be a list
                of 1D NumPy arrays, each array containing the waveform data received on one channel, in channel order.
                The Waveform object also has a timestamp attribute, which (if timestamping was enabled in acquisition
                settings) contains the time at which the acquisition was triggered.
        """
        if self._acquisition_mode != AcquisitionMode.SPC_REC_STD_SINGLE:
            raise SpectrumWrongAcquisitionMode(
                "Set the acquisition mode to SPC_REC_STD_SINGLE using "
                "configure_acquisition() or set_acquisition_mode() before executing "
                "a standard single mode acquisition."
            )
        self.start_acquisition()
        self.wait_for_acquisition_to_complete()
        self.define_transfer_buffer()
        self.start_transfer()
        self.wait_for_transfer_to_complete()
        waveforms = self.get_waveforms()
        self.stop_acquisition()  # Only strictly required for Mock devices. Should have not effect on hardware.
        return Measurement(waveforms=waveforms, timestamp=self.get_timestamp())

    def execute_finite_multi_fifo_acquisition(self, num_measurements: int) -> List[Measurement]:
        """Carry out a finite number of Multi FIFO mode measurements and then stop the acquisitions.

        This method automatically carries out a defined number of measurement in Multi FIFO mode, including handling the
        creation of a `TransferBuffer`, streaming the acquired waveforms to the PC, terminating the acquisition and
        returning the acquired waveforms. After being called, it will wait for the requested number of triggers to be
        received, generating the correct number of measurements. It retrieves each measurement's waveforms from the
        `TransferBuffer` as they arrive. Once the requested number of measurements have been received, the acquisition
        is terminated and the waveforms are returned. The device must be configured in SPC_REC_FIFO_MULTI acquisition
        mode.

        Args:
            num_measurements (int): The number of measurements to carry out, each triggered by subsequent trigger
                events.
        Returns:
            measurements (List[Measurement]): A list of Measurement objects with length `num_measurements`. Each
                Measurement object has a `waveforms` attribute containing a list of 1D NumPy arrays. Each array is a
                waveform acquired from one channel. The arrays are in channel order. The Waveform objects also have a
                timestamp attribute, which (if timestamping was enabled in acquisition settings) contains the time at
                which the acquisition was triggered.
        """
        self.execute_continuous_multi_fifo_acquisition()
        measurements = []
        for _ in range(num_measurements):
            measurements.append(Measurement(waveforms=self.get_waveforms(), timestamp=self.get_timestamp()))
        self.stop_acquisition()
        return measurements

    def execute_continuous_multi_fifo_acquisition(self) -> None:
        """Start a continuous Multi FIFO mode acquisition.

        This method automatically starts acquiring and streaming samples in Multi FIFO mode, including handling the
        creation of a `TransferBuffer` and streaming the acquired waveforms to the PC. It will return almost
        instantaneously. The acquired waveforms must then be read out of the transfer buffer in a loop using the
        `get_waveforms()` method. Waveforms must be read at least as fast as they are being acquired.
        The FIFO acquisition and streaming will continue until `stop_acquisition()` is called. The device
        must be configured in SPC_REC_FIFO_MULTI acquisition mode."""
        if self._acquisition_mode != AcquisitionMode.SPC_REC_FIFO_MULTI:
            raise SpectrumWrongAcquisitionMode(
                "Set the acquisition mode to SPC_REC_FIFO_MULTI using "
                "configure_acquisition() or set_acquisition_mode() before executing "
                "a multi fifo mode acquisition."
            )
        self.define_transfer_buffer()
        self.start_acquisition()
        self.start_transfer()

    def write_to_spectrum_device_register(
        self,
        spectrum_register: int,
        value: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> None:
        """Set the value of a register on the Spectrum digitiser.

        This method is used internally by `SpectrumDevice` and its subclasses to configure a hardware device, but can
        also used to set the value of registers that are not implemented in `SpectrumDevice` and its subclasses.

        Args:
            spectrum_register (int): Identifier of the register to set. This should be a global constant imported from
                regs.py in the spectrum_gmbh package.
            value (int): Value to write to the register. This should be a global constant imported from
                regs.py in the spectrum_gmbh package.
            length (`SpectrumRegisterLength`): A `SpectrumRegisterLength` object specifying the length of the register
                to set, in bits.
        """
        if not SPECTRUM_DRIVERS_FOUND:
            raise SpectrumDriversNotFound(
                "Cannot communicate with hardware. For testing on a system without drivers or connected hardware, use"
                " MockSpectrumCard instead."
            )
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
        """Get the value of a register on the Spectrum digitiser.

        This method is used internally by `SpectrumDevice` and its subclasses to read the configuration of a hardware
        device, but can be also used to get the value of registers that are not implemented in
        SpectrumDevice and its subclasses.

        Args:
            spectrum_register (int): Identifier of the register to set. This should be a global constant imported from
                spectrum_gmbh.regs.
            length (`SpectrumRegisterLength`): A `SpectrumRegisterLength` object specifying the length of the register
                to set, in bits.

        Returns:
            value (int): Value of the register. This can be matched to a global constant imported from
                spectrum_gmbh.regs, usually using one of the Enums defined in the settings module.
        """
        if not SPECTRUM_DRIVERS_FOUND:
            raise SpectrumDriversNotFound(
                "Cannot communicate with hardware. For testing on a system without drivers or connected hardware, use"
                " a MockSpectrumDevice instead (i.e. MockSpectrumCard or MockSpectrumStarHub)."
            )
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
