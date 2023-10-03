"""Provides a concrete class for configuring the individual channels of Spectrum digitiser devices."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from numpy import ndarray

from spectrum_gmbh.regs import SPC_MIINST_MAXADCVALUE
from spectrumdevice.devices.abstract_device import AbstractSpectrumCard, AbstractSpectrumChannel
from spectrumdevice.devices.digitiser.digitiser_interface import (
    SpectrumDigitiserChannelInterface,
)
from spectrumdevice.exceptions import SpectrumCardIsNotADigitiser
from spectrumdevice.settings.card_dependent_properties import CardType
from spectrumdevice.settings.channel import VERTICAL_OFFSET_COMMANDS, VERTICAL_RANGE_COMMANDS


class SpectrumDigitiserChannel(AbstractSpectrumChannel, SpectrumDigitiserChannelInterface):
    """Class for controlling an individual channel of a spectrum digitiser. Channels are constructed automatically when
    a `SpectrumDigitiserCard` or `SpectrumDigitiserStarHub` is instantiated, and can then be accessed via the
    `.channels` property."""

    def __init__(self, channel_number: int, parent_device: AbstractSpectrumCard):

        if parent_device.type != CardType.SPCM_TYPE_AI:
            raise SpectrumCardIsNotADigitiser(parent_device.type)
        AbstractSpectrumChannel.__init__(self, channel_number, parent_device)
        self._full_scale_value = self._parent_device.read_spectrum_device_register(SPC_MIINST_MAXADCVALUE)
        # used frequently so store locally instead of reading from device each time:
        self._vertical_range_mv = self.vertical_range_in_mv
        self._vertical_offset_in_percent = self.vertical_offset_in_percent

    def convert_raw_waveform_to_voltage_waveform(self, raw_waveform: ndarray) -> ndarray:
        vertical_offset_mv = 0.01 * float(self._vertical_range_mv * self._vertical_offset_in_percent)
        return 1e-3 * (
            float(self._vertical_range_mv) * raw_waveform / float(self._full_scale_value) + vertical_offset_mv
        )

    @property
    def vertical_range_in_mv(self) -> int:
        """The currently set input range of the channel in mV.

        Returns:
            vertical_range (int): The currently set vertical range in mV.
        """
        self._vertical_range_mv = self._parent_device.read_spectrum_device_register(
            VERTICAL_RANGE_COMMANDS[self._number]
        )
        return self._vertical_range_mv

    def set_vertical_range_in_mv(self, vertical_range: int) -> None:
        """Set the input range of the channel in mV. See Spectrum documentation for valid values.

        Args:
            vertical_range (int): The desired vertical range in mV.
        """
        self._parent_device.write_to_spectrum_device_register(VERTICAL_RANGE_COMMANDS[self._number], vertical_range)
        self._vertical_range_mv = vertical_range

    @property
    def vertical_offset_in_percent(self) -> int:
        """The currently set input offset of the channel in percent of the vertical range.

        Returns:
            offset (int): The currently set vertical offset in percent.
        """
        self._vertical_offset_in_percent = self._parent_device.read_spectrum_device_register(
            VERTICAL_OFFSET_COMMANDS[self._number]
        )
        return self._vertical_offset_in_percent

    def set_vertical_offset_in_percent(self, offset: int) -> None:
        """Set the input offset of the channel in percent of the vertical range. See spectrum documentation for valid
        values.

        Args:
            offset (int): The desired vertical offset in percent.
        """
        self._parent_device.write_to_spectrum_device_register(VERTICAL_OFFSET_COMMANDS[self._number], offset)
        self._vertical_offset_in_percent = offset
