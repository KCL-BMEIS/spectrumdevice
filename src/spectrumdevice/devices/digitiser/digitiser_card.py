"""Provides a concrete class for controlling an individual Spectrum digitiser abstract_device."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.
import datetime
import logging
from typing import List, Optional, Sequence, cast

from numpy import float_, mod
from numpy.typing import NDArray

from spectrum_gmbh.regs import (
    M2CMD_CARD_WAITREADY,
    SPC_AVERAGES,
    SPC_CARDMODE,
    SPC_DATA_AVAIL_CARD_LEN,
    SPC_DATA_AVAIL_USER_LEN,
    SPC_M2CMD,
    SPC_MEMSIZE,
    SPC_MIINST_CHPERMODULE,
    SPC_MIINST_MODULES,
    SPC_POSTTRIGGER,
    SPC_SEGMENTSIZE,
)
from spectrumdevice.devices.abstract_device.abstract_spectrum_card import AbstractSpectrumCard
from spectrumdevice.devices.digitiser.abstract_spectrum_digitiser import AbstractSpectrumDigitiser
from spectrumdevice.devices.digitiser.digitiser_interface import SpectrumDigitiserChannelInterface
from spectrumdevice import SpectrumDigitiserChannel
from spectrumdevice.devices.spectrum_timestamper import Timestamper
from spectrumdevice.exceptions import (
    SpectrumNoTransferBufferDefined,
)
from spectrumdevice.settings import CardToPCDataTransferBuffer
from spectrumdevice.settings.card_dependent_properties import get_memsize_step_size
from spectrumdevice.settings.device_modes import AcquisitionMode
from spectrumdevice.settings.transfer_buffer import set_transfer_buffer

logger = logging.getLogger(__name__)


class SpectrumDigitiserCard(AbstractSpectrumCard, AbstractSpectrumDigitiser):
    """Class for controlling individual Spectrum digitiser cards."""

    def __init__(self, device_number: int = 0, ip_address: Optional[str] = None):
        """
        Args:
            device_number (int): Index of the card to control. If only one card is present, set to 0.
            ip_address (Optional[str]): If connecting to a networked card, provide the IP address here as a string.

        """
        AbstractSpectrumCard.__init__(self, device_number, ip_address)
        self._acquisition_mode = self.acquisition_mode
        self._timestamper: Optional[Timestamper] = None

    def _init_channels(self) -> Sequence[SpectrumDigitiserChannelInterface]:
        num_modules = self.read_spectrum_device_register(SPC_MIINST_MODULES)
        num_channels_per_module = self.read_spectrum_device_register(SPC_MIINST_CHPERMODULE)
        total_channels = num_modules * num_channels_per_module
        return tuple([SpectrumDigitiserChannel(n, self) for n in range(total_channels)])

    def enable_timestamping(self) -> None:
        self._timestamper = Timestamper(self, self._handle)

    def wait_for_acquisition_to_complete(self) -> None:
        """Blocks until the current acquisition has finished, or the timeout is reached.

        In Standard Single mode (SPC_REC_STD_SINGLE), this should be called after `start_acquisition()`. Once the call
            to `wait_for_acquisition_to_complete()` returns, the newly acquired samples are in the on_device buffer and
            ready for transfer to the `TransferBuffer` using `start_transfer()`.

        In FIFO mode (SPC_REC_FIFO_MULTI), the card will continue to acquire samples until
            `stop_acquisition()` is called, so `wait_for_acquisition_to_complete()` should not be used.

        """
        self.write_to_spectrum_device_register(SPC_M2CMD, M2CMD_CARD_WAITREADY)

    def get_waveforms(self) -> List[NDArray[float_]]:
        """Get a list of the most recently transferred waveforms, in channel order.

        This method copies and reshapes the samples in the `TransferBuffer` into a list of 1D NumPy arrays (waveforms)
        and returns the list.

        In Standard Single mode (SPC_REC_STD_SINGLE), `get_waveforms()` should be called after
        `wait_for_transfer_to_complete()` has returned.

        In FIFO mode (SPC_REC_FIFO_MULTI), while the card is continuously acquiring samples and transferring them to the
        `TransferBuffer`, this method should be called in a loop . The method will block until each new transfer is
        received, so the loop will run at the same rate as the acquisition (in SPC_REC_FIFO_MULTI mode, for example,
        this would the rate at which your trigger source was running).

        Returns:
            waveforms (List[NDArray[float_]]): A list of 1D NumPy arrays, one for each channel enabled for the
                acquisition, ordered by channel number.

        """
        num_available_bytes = 0
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            self.wait_for_transfer_to_complete()
            num_available_bytes = self.read_spectrum_device_register(SPC_DATA_AVAIL_USER_LEN)

        if self._transfer_buffer is not None:
            num_expected_bytes_per_frame = self._transfer_buffer.data_array_length_in_bytes
            if num_available_bytes > num_expected_bytes_per_frame:
                num_available_bytes = num_expected_bytes_per_frame
        else:
            raise SpectrumNoTransferBufferDefined("Cannot find a samples transfer buffer")

        waveforms_in_columns = (
            self.transfer_buffers[0]
            .copy_contents()
            .reshape((self.acquisition_length_in_samples, len(self.enabled_channels)))
        )
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            self.write_to_spectrum_device_register(SPC_DATA_AVAIL_CARD_LEN, num_available_bytes)

        voltage_waveforms = [
            cast(SpectrumDigitiserChannel, ch).convert_raw_waveform_to_voltage_waveform(waveform)
            for ch, waveform in zip(self.channels, waveforms_in_columns.T)
        ]

        return voltage_waveforms

    def get_timestamp(self) -> Optional[datetime.datetime]:
        """Get timestamp for the last acquisition"""
        if self._timestamper is not None:
            return self._timestamper.get_timestamp()
        else:
            return None

    @property
    def acquisition_length_in_samples(self) -> int:
        """The current recording length (per channel) in samples.

        Returns:
            length_in_samples (int): The current recording length ('acquisition length') in samples."""
        return self.read_spectrum_device_register(SPC_MEMSIZE)

    def set_acquisition_length_in_samples(self, length_in_samples: int) -> None:
        """Change the recording length (per channel). In FIFO mode, it will be quantised according to the step size
          allowed by the connected card type.

        Args:
            length_in_samples (int): The desired recording length ('acquisition length'), in samples.
        """
        length_in_samples = self._coerce_num_samples_if_fifo(length_in_samples)
        self.write_to_spectrum_device_register(SPC_SEGMENTSIZE, length_in_samples)
        self.write_to_spectrum_device_register(SPC_MEMSIZE, length_in_samples)

    @property
    def post_trigger_length_in_samples(self) -> int:
        """The number of samples of the recording that will contain data received after the trigger event.

        Returns:
            length_in_samples (int): The currently set post trigger length in samples.
        """
        return self.read_spectrum_device_register(SPC_POSTTRIGGER)

    def set_post_trigger_length_in_samples(self, length_in_samples: int) -> None:
        """Change the number of samples of the recording that will contain data received after the trigger event.
        In FIFO mode, this will be quantised according to the minimum step size allowed by the connected card.

        Args:
            length_in_samples (int): The desired post trigger length in samples."""
        length_in_samples = self._coerce_num_samples_if_fifo(length_in_samples)
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            if (self.acquisition_length_in_samples - length_in_samples) < get_memsize_step_size(self._card_type):
                logger.warning(
                    "FIFO mode: coercing post trigger length to maximum allowed value (step-size samples less than "
                    "the acquisition length)."
                )
                length_in_samples = self.acquisition_length_in_samples - get_memsize_step_size(self._card_type)
        self.write_to_spectrum_device_register(SPC_POSTTRIGGER, length_in_samples)

    def _coerce_num_samples_if_fifo(self, value: int) -> int:
        if self.acquisition_mode == AcquisitionMode.SPC_REC_FIFO_MULTI:
            if value != mod(value, get_memsize_step_size(self._card_type)):
                logger.warning(
                    f"FIFO mode: coercing length to nearest {get_memsize_step_size(self._card_type)}" f" samples"
                )
                value = int(value - mod(value, get_memsize_step_size(self._card_type)))
        return value

    @property
    def number_of_averages(self) -> int:
        return self.read_spectrum_device_register(SPC_AVERAGES)

    def set_number_of_averages(self, num_averages: int) -> None:
        if num_averages > 0:
            self.write_to_spectrum_device_register(SPC_AVERAGES, num_averages)
        else:
            raise ValueError("Number of averages must be greater than 0.")

    @property
    def acquisition_mode(self) -> AcquisitionMode:
        """The currently enabled card mode. Will raise an exception if the current mode is not supported by
        `spectrumdevice`.

        Returns:
            mode (`AcquisitionMode`): The currently enabled card acquisition mode."""
        return AcquisitionMode(self.read_spectrum_device_register(SPC_CARDMODE))

    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        """Change the currently enabled card mode. See `AcquisitionMode` and the Spectrum documentation
        for the available modes.

        Args:
            mode (`AcquisitionMode`): The desired acquisition mode."""
        self.write_to_spectrum_device_register(SPC_CARDMODE, mode.value)

    def define_transfer_buffer(self, buffer: Optional[List[CardToPCDataTransferBuffer]] = None) -> None:
        """Create or provide a `CardToPCDataTransferBuffer` object for receiving acquired samples from the abstract_device.

        If no buffer is provided, one will be created with the correct size and a board_memory_offset_bytes of 0. A
        seperate buffer for transfering Timestamps will also be created using the Timestamper class.

        Args:
            buffer (Optional[List[`CardToPCDataTransferBuffer`]]): A length-1 list containing a pre-constructed
                `CardToPCDataTransferBuffer`  The size of the buffer should be chosen according to the current number of
                active channels and the acquisition length.
        """
        if buffer:
            self._transfer_buffer = buffer[0]
        else:
            self._transfer_buffer = CardToPCDataTransferBuffer(
                self.acquisition_length_in_samples * len(self.enabled_channels)
            )
        set_transfer_buffer(self._handle, self._transfer_buffer)

    def __str__(self) -> str:
        return f"Card {self._visa_string}"


def _create_visa_string_from_ip(ip_address: str, instrument_number: int) -> str:
    return f"TCPIP[0]::{ip_address}::inst{instrument_number}::INSTR"
