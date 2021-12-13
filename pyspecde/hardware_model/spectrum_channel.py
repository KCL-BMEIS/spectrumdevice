from pyspecde.spectrum_api_wrapper.channel import VERTICAL_RANGE_COMMANDS, VERTICAL_OFFSET_COMMANDS, SpectrumChannelName
from pyspecde.hardware_model.spectrum_interface import SpectrumChannelInterface, SpectrumDeviceInterface


class SpectrumChannel(SpectrumChannelInterface):
    def __init__(self, name: SpectrumChannelName, parent_device: SpectrumDeviceInterface):
        self._name: SpectrumChannelName = name
        self._parent_device = parent_device
        self._enabled = True

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SpectrumChannel):
            return (self.name == other.name) and (self._parent_device == other._parent_device)
        else:
            raise NotImplementedError()

    def __str__(self) -> str:
        return f"{self._name.name} of device {self._parent_device}"

    def __repr__(self) -> str:
        return str(self)

    @property
    def name(self) -> SpectrumChannelName:
        return self._name

    @property
    def _number(self) -> int:
        return int(self.name.name.split("CHANNEL")[-1])

    @property
    def vertical_range_mv(self) -> int:
        return self._parent_device.get_spectrum_api_param(VERTICAL_RANGE_COMMANDS[self._number])

    def set_vertical_range_mv(self, vertical_range: int) -> None:
        self._parent_device.set_spectrum_api_param(VERTICAL_RANGE_COMMANDS[self._number], vertical_range)

    @property
    def vertical_offset_percent(self) -> int:
        return self._parent_device.get_spectrum_api_param(VERTICAL_OFFSET_COMMANDS[self._number])

    def set_vertical_offset_percent(self, offset: int) -> None:
        self._parent_device.set_spectrum_api_param(VERTICAL_OFFSET_COMMANDS[self._number], offset)


def spectrum_channel_factory(channel_number: int, parent_device: SpectrumDeviceInterface) -> SpectrumChannel:
    return SpectrumChannel(SpectrumChannelName[f"CHANNEL{channel_number}"], parent_device)
