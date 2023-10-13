"""Defines a part-implemented abstract superclass for all Spectrum digitiser devices."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from abc import ABC
from typing import List, cast

from spectrumdevice.measurement import Measurement
from spectrumdevice.devices.abstract_device import AbstractSpectrumDevice
from spectrumdevice.devices.digitiser.digitiser_interface import SpectrumDigitiserInterface
from spectrumdevice.devices.digitiser.digitiser_channel import SpectrumDigitiserChannel
from spectrumdevice.exceptions import SpectrumWrongAcquisitionMode
from spectrumdevice.settings import AcquisitionMode, AcquisitionSettings
from spectrum_gmbh.regs import M2CMD_CARD_WRITESETUP, SPC_M2CMD


class AbstractSpectrumDigitiser(SpectrumDigitiserInterface, AbstractSpectrumDevice, ABC):
    """Abstract superclass which implements methods common to all Spectrum digitiser devices. Instances of this class
    cannot be constructed directly. Instead, construct instances of the concrete classes (`SpectrumDigitiserCard`,
    `SpectrumDigitiserStarHub` or their mock equivalents) which inherit the methods defined here. Note that
    the mock devices override several of the methods defined here."""

    def configure_acquisition(self, settings: AcquisitionSettings) -> None:
        """Apply all the settings contained in an `AcquisitionSettings` dataclass to the device.

        Args:
            settings (`AcquisitionSettings`): An `AcquisitionSettings` dataclass containing the setting values to apply.
        """
        if settings.batch_size > 1 and settings.acquisition_mode == AcquisitionMode.SPC_REC_STD_SINGLE:
            raise ValueError("In standard single mode, only 1 acquisition can be downloaded at a time.")
        self._acquisition_mode = settings.acquisition_mode
        self.set_batch_size(settings.batch_size)
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
            cast(SpectrumDigitiserChannel, channel).set_vertical_range_in_mv(v_range)
            cast(SpectrumDigitiserChannel, channel).set_vertical_offset_in_percent(v_offset)

        # Write the configuration to the card
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_WRITESETUP)

        if settings.timestamping_enabled:
            self.enable_timestamping()

    def execute_standard_single_acquisition(self) -> Measurement:
        """Carry out a single measurement in standard single mode and return the acquired waveforms.

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
        self.start()
        self.wait_for_acquisition_to_complete()
        self.define_transfer_buffer()
        self.start_transfer()
        self.wait_for_transfer_chunk_to_complete()
        waveforms = self.get_waveforms()[0]
        self.stop()  # Only strictly required for Mock devices. Should not affect hardware.
        return Measurement(waveforms=waveforms, timestamp=self.get_timestamp())

    def execute_finite_fifo_acquisition(self, num_measurements: int) -> List[Measurement]:
        """Carry out a finite number of FIFO mode measurements and then stop the acquisitions.

        This method automatically carries out a defined number of measurement in Multi FIFO mode, including handling the
        creation of a `TransferBuffer`, streaming the acquired waveforms to the PC, terminating the acquisition and
        returning the acquired waveforms. After being called, it will wait for the requested number of triggers to be
        received, generating the correct number of measurements. It retrieves each measurement's waveforms from the
        `TransferBuffer` as they arrive. Once the requested number of measurements have been received, the acquisition
        is terminated and the waveforms are returned. The device must be configured in SPC_REC_FIFO_MULTI or
        SPC_REC_FIFO_AVERAGE acquisition mode.

        Args:
            num_measurements (int): The number of measurements to carry out.
        Returns:
            measurements (List[Measurement]): A list of Measurement objects with length `num_measurements`. Each
                Measurement object has a `waveforms` attribute containing a list of 1D NumPy arrays. Each array is a
                waveform acquired from one channel. The arrays are in channel order. The Waveform objects also have a
                timestamp attribute, which (if timestamping was enabled in acquisition settings) contains the time at
                which the acquisition was triggered.
        """
        if (num_measurements % self.batch_size) != 0:
            raise ValueError(
                "Number of measurements in a finite FIFO acquisition must be a multiple of the "
                " batch size configured using AbstractSpectrumDigitiser.configure_acquisition()."
            )
        self.execute_continuous_fifo_acquisition()
        measurements = []
        for _ in range(num_measurements // self.batch_size):
            measurements += [
                Measurement(waveforms=frame, timestamp=self.get_timestamp()) for frame in self.get_waveforms()
            ]
        self.stop()
        return measurements

    def execute_continuous_fifo_acquisition(self) -> None:
        """Start a continuous FIFO mode acquisition.

        This method automatically starts acquiring and streaming samples in FIFO mode, including handling the
        creation of a `TransferBuffer` and streaming the acquired waveforms to the PC. It will return almost
        instantaneously. The acquired waveforms must then be read out of the transfer buffer in a loop using the
        `get_waveforms()` method. Waveforms must be read at least as fast as they are being acquired.
        The FIFO acquisition and streaming will continue until `stop_acquisition()` is called. The device
        must be configured in SPC_REC_FIFO_MULTI or SPC_REC_FIFO_AVERAGE acquisition mode."""
        if self._acquisition_mode not in (AcquisitionMode.SPC_REC_FIFO_MULTI, AcquisitionMode.SPC_REC_FIFO_AVERAGE):
            raise SpectrumWrongAcquisitionMode(
                "Set the acquisition mode to SPC_REC_FIFO_MULTI or SPC_REC_FIFO_AVERAGE using "
                "configure_acquisition() or set_acquisition_mode() before executing "
                "a fifo mode acquisition."
            )
        self.define_transfer_buffer()
        self.start()
        self.start_transfer()
