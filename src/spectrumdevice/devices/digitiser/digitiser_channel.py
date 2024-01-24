"""Provides a concrete class for configuring the individual channels of Spectrum digitiser devices."""
from typing import Any

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from numpy import ndarray

from spectrum_gmbh.py_header.regs import SPC_MIINST_MAXADCVALUE
from spectrumdevice.devices.abstract_device import AbstractSpectrumCard
from spectrumdevice.devices.abstract_device.abstract_spectrum_channel import AbstractSpectrumAnalogChannel
from spectrumdevice.devices.abstract_device.abstract_spectrum_io_line import AbstractSpectrumIOLine
from spectrumdevice.devices.digitiser.digitiser_interface import (
    SpectrumDigitiserInterface,
    SpectrumDigitiserAnalogChannelInterface,
    SpectrumDigitiserIOLineInterface,
)
from spectrumdevice.exceptions import SpectrumCardIsNotADigitiser
from spectrumdevice.settings import IOLineMode
from spectrumdevice.settings.card_dependent_properties import CardType
from spectrumdevice.settings.channel import (
    INPUT_IMPEDANCE_COMMANDS,
    InputImpedance,
    VERTICAL_OFFSET_COMMANDS,
    VERTICAL_RANGE_COMMANDS,
    InputCoupling,
    INPUT_COUPLING_COMMANDS,
    InputPath,
    INPUT_PATH_COMMANDS,
)


class SpectrumDigitiserIOLine(AbstractSpectrumIOLine, SpectrumDigitiserIOLineInterface):
    """Class for controlling multipurpose IO lines of a digitiser, e.g. X0, X1, X2 and X3."""

    def __init__(self, parent_device: AbstractSpectrumCard, **kwargs: Any) -> None:
        if parent_device.type != CardType.SPCM_TYPE_AI:
            raise SpectrumCardIsNotADigitiser(parent_device.type)
        super().__init__(parent_device=parent_device, **kwargs)  # pass unused args up the inheritance hierarchy

    def _get_io_line_mode_settings_mask(self, mode: IOLineMode) -> int:
        return 0  # no settings required for DigOut


class SpectrumDigitiserAnalogChannel(AbstractSpectrumAnalogChannel, SpectrumDigitiserAnalogChannelInterface):
    """Class for controlling an individual channel of a spectrum digitiser. Channels are constructed automatically when
    a `SpectrumDigitiserCard` or `SpectrumDigitiserStarHub` is instantiated, and can then be accessed via the
    `.channels` property."""

    def __init__(self, channel_number: int, parent_device: SpectrumDigitiserInterface) -> None:

        if parent_device.type != CardType.SPCM_TYPE_AI:
            raise SpectrumCardIsNotADigitiser(parent_device.type)

        # pass unused args up the inheritance hierarchy
        super().__init__(channel_number=channel_number, parent_device=parent_device)

        self._full_scale_value = self._parent_device.read_spectrum_device_register(SPC_MIINST_MAXADCVALUE)
        # used frequently so store locally instead of reading from device each time:
        self._vertical_range_mv = self.vertical_range_in_mv
        self._vertical_offset_in_percent = self.vertical_offset_in_percent

    def _get_settings_as_dict(self) -> dict:
        return {
            SpectrumDigitiserAnalogChannel.input_path.__name__: self.input_path,
            SpectrumDigitiserAnalogChannel.input_coupling.__name__: self.input_coupling,
            SpectrumDigitiserAnalogChannel.input_impedance.__name__: self.input_impedance,
            SpectrumDigitiserAnalogChannel.vertical_range_in_mv.__name__: self.vertical_range_in_mv,
            SpectrumDigitiserAnalogChannel.vertical_offset_in_percent.__name__: self.vertical_offset_in_percent,
        }

    def _set_settings_from_dict(self, settings: dict) -> None:
        self.set_input_path(settings[SpectrumDigitiserAnalogChannel.input_path.__name__])
        self.set_input_coupling(settings[SpectrumDigitiserAnalogChannel.input_coupling.__name__])
        self.set_input_impedance(settings[SpectrumDigitiserAnalogChannel.input_impedance.__name__])
        self.set_vertical_range_in_mv(settings[SpectrumDigitiserAnalogChannel.vertical_range_in_mv.__name__])
        self.set_vertical_offset_in_percent(
            settings[SpectrumDigitiserAnalogChannel.vertical_offset_in_percent.__name__]
        )

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

    @property
    def input_impedance(self) -> InputImpedance:
        """The current input impedance setting of the channel (50 Ohm or 1 MOhm)"""
        impedance_binary_value = self._parent_device.read_spectrum_device_register(
            INPUT_IMPEDANCE_COMMANDS[self._number]
        )
        return InputImpedance(impedance_binary_value)

    def set_input_impedance(self, input_impedance: InputImpedance) -> None:
        self._parent_device.write_to_spectrum_device_register(
            INPUT_IMPEDANCE_COMMANDS[self._number], input_impedance.value
        )

    @property
    def input_coupling(self) -> InputCoupling:
        """The coupling (AC or DC) setting of the channel. Only available on some hardware."""
        coupling_binary_value = self._parent_device.read_spectrum_device_register(INPUT_COUPLING_COMMANDS[self._number])
        return InputCoupling(coupling_binary_value)

    def set_input_coupling(self, input_coupling: InputCoupling) -> None:
        self._parent_device.write_to_spectrum_device_register(
            INPUT_COUPLING_COMMANDS[self._number], input_coupling.value
        )

    @property
    def input_path(self) -> InputPath:
        """The input path setting of the channel. Only available on some hardware."""
        path_binary_value = self._parent_device.read_spectrum_device_register(INPUT_PATH_COMMANDS[self._number])
        return InputPath(path_binary_value)

    def set_input_path(self, input_path: InputPath) -> None:
        self._parent_device.write_to_spectrum_device_register(INPUT_PATH_COMMANDS[self._number], input_path.value)
