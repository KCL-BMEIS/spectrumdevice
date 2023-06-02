"""Provides a partially-implemented abstract class common to individual channels of Spectrum devices."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from spectrumdevice.devices.abstract_device.device_interface import SpectrumChannelInterface
from spectrumdevice.devices.abstract_device.abstract_spectrum_card import AbstractSpectrumCard
from spectrumdevice.settings.channel import SpectrumChannelName


class AbstractSpectrumChannel(SpectrumChannelInterface):
    """Partially implemented abstract superclass contain code common for controlling an individual channel of all
    spectrum devices."""

    def __init__(self, channel_number: int, parent_device: AbstractSpectrumCard):
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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AbstractSpectrumChannel):
            return (self.name == other.name) and (self._parent_device == other._parent_device)
        else:
            raise NotImplementedError()

    def __str__(self) -> str:
        return f"{self._name.name} of {self._parent_device}"

    def __repr__(self) -> str:
        return str(self)
