"""Provides a concrete class for configuring the individual channels of Spectrum digitiser devices."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from spectrumdevice.settings.channel import VERTICAL_RANGE_COMMANDS, VERTICAL_OFFSET_COMMANDS, SpectrumChannelName
from spectrumdevice.devices.spectrum_interface import SpectrumChannelInterface, SpectrumDeviceInterface


class SpectrumChannel(SpectrumChannelInterface):
    """Class for controlling an individual channel of a spectrum digitiser. Channels are constructed automatically when
    a SpectrumDevice is instantiated, and accessed via the `SpectrumDevice.channels` property."""

    def __init__(self, channel_number: int, parent_device: SpectrumDeviceInterface):
        self._name = SpectrumChannelName[f"CHANNEL{channel_number}"]
        self._parent_device = parent_device
        self._enabled = True

    @property
    def name(self) -> SpectrumChannelName:
        """The identifier assigned by the spectrum driver, formatted as an Enum by the settings package.

        Returns:
            name (`SpectrumChannelName`): The name of the channel, as assigned by the driver."""
        return self._name

    @property
    def _number(self) -> int:
        return int(self.name.name.split("CHANNEL")[-1])

    @property
    def vertical_range_in_mv(self) -> int:
        """The currently set input range of the channel in mV.

        Returns:
            vertical_range (int): The currently set vertical range in mV.
        """
        return self._parent_device.read_spectrum_device_register(VERTICAL_RANGE_COMMANDS[self._number])

    def set_vertical_range_in_mv(self, vertical_range: int) -> None:
        """Set the input range of the channel in mV. See Spectrum documentation for valid values.

        Args:
            vertical_range (int): The desired vertical range in mV.
        """
        self._parent_device.write_to_spectrum_device_register(VERTICAL_RANGE_COMMANDS[self._number], vertical_range)

    @property
    def vertical_offset_in_percent(self) -> int:
        """The currently set input offset of the channel in percent of the vertical range.

        Returns:
            offset (int): The currently set vertical offset in percent.
        """
        return self._parent_device.read_spectrum_device_register(VERTICAL_OFFSET_COMMANDS[self._number])

    def set_vertical_offset_in_percent(self, offset: int) -> None:
        """Set the input offset of the channel in percent of the vertical range. See spectrum documentation for valid
        values.

        Args:
            offset (int): The desired vertical offset in percent.
        """
        self._parent_device.write_to_spectrum_device_register(VERTICAL_OFFSET_COMMANDS[self._number], offset)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SpectrumChannel):
            return (self.name == other.name) and (self._parent_device == other._parent_device)
        else:
            raise NotImplementedError()

    def __str__(self) -> str:
        return f"{self._name.name} of {self._parent_device}"

    def __repr__(self) -> str:
        return str(self)
