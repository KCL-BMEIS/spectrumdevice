from functools import reduce
from operator import or_
from typing import List, Sequence

from pyspecde.spectrum_device import networked_spectrum_device_factory
from pyspecde.spectrum_exceptions import SpectrumSettingsMismatchError
from pyspecde.spectrum_interface import (
    SpectrumInterface,
    AcquisitionMode,
    TriggerSource,
    ClockMode,
    SpectrumChannelInterface,
    SpectrumIntLengths,
)


class SpectrumNetbox(SpectrumInterface):
    def __init__(self, devices: Sequence[SpectrumInterface]):
        self._devices = devices
        self.apply_channel_enabling()

    @property
    def channels(self) -> List[SpectrumChannelInterface]:
        channels = []
        for device in self._devices:
            channels += device.channels
        return channels

    def apply_channel_enabling(self) -> None:
        for d in self._devices:
            d.apply_channel_enabling()

    @property
    def acquisition_length_bytes(self) -> int:
        lengths = []
        for d in self._devices:
            lengths.append(d.acquisition_length_bytes)
        return check_settings_constant_across_devices(lengths, __name__)

    @acquisition_length_bytes.setter
    def acquisition_length_bytes(self, length_in_bytes: int) -> None:
        for d in self._devices:
            d.acquisition_length_bytes = length_in_bytes  # type: ignore

    @property
    def post_trigger_length_bytes(self) -> int:
        lengths = []
        for d in self._devices:
            lengths.append(d.post_trigger_length_bytes)
        return check_settings_constant_across_devices(lengths, __name__)

    @post_trigger_length_bytes.setter
    def post_trigger_length_bytes(self, length_in_bytes: int) -> None:
        for d in self._devices:
            d.post_trigger_length_bytes = length_in_bytes  # type: ignore

    @property
    def acquisition_mode(self) -> AcquisitionMode:
        modes = []
        for d in self._devices:
            modes.append(d.acquisition_mode)
        return AcquisitionMode(check_settings_constant_across_devices([m.value for m in modes], __name__))

    @acquisition_mode.setter
    def acquisition_mode(self, mode: AcquisitionMode) -> None:
        for d in self._devices:
            d.acquisition_mode = mode  # type: ignore

    @property
    def timeout_ms(self) -> int:
        timeouts = []
        for d in self._devices:
            timeouts.append(d.timeout_ms)
        return check_settings_constant_across_devices(timeouts, __name__)

    @timeout_ms.setter
    def timeout_ms(self, timeout_ms: int) -> None:
        for d in self._devices:
            d.timeout_ms = timeout_ms  # type: ignore

    @property
    def trigger_sources(self) -> List[TriggerSource]:
        sources_all_devices = []
        or_of_sources = []
        for d in self._devices:
            sources_all_devices.append(d.trigger_sources)
            or_of_sources.append(reduce(or_, [s.value for s in d.trigger_sources]))
        check_settings_constant_across_devices(or_of_sources, __name__)
        return sources_all_devices[0]

    @trigger_sources.setter
    def trigger_sources(self, sources: List[TriggerSource]) -> None:
        for d in self._devices:
            d.trigger_sources = sources  # type: ignore

    @property
    def clock_mode(self) -> ClockMode:
        modes = []
        for d in self._devices:
            modes.append(d.clock_mode)
        return ClockMode(check_settings_constant_across_devices([m.value for m in modes], __name__))

    @clock_mode.setter
    def clock_mode(self, mode: ClockMode) -> None:
        for d in self._devices:
            d.clock_mode = mode  # type: ignore

    @property
    def sample_rate_hz(self) -> int:
        rates = []
        for d in self._devices:
            rates.append(d.sample_rate_hz)
        return check_settings_constant_across_devices(rates, __name__)

    @sample_rate_hz.setter
    def sample_rate_hz(self, rate: int) -> None:
        for d in self._devices:
            d.sample_rate_hz = rate  # type: ignore

    def disconnect(self) -> None:
        for d in self._devices:
            d.disconnect()

    def set_spectrum_api_param(
        self,
        spectrum_command: int,
        value: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> None:
        for device in self._devices:
            device.set_spectrum_api_param(spectrum_command, value, length)

    def get_spectrum_api_param(
        self,
        spectrum_command: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> int:
        param_values_each_device = self.get_spectrum_api_param_all_devices(spectrum_command, length)
        return check_settings_constant_across_devices(param_values_each_device, str(spectrum_command))

    def get_spectrum_api_param_all_devices(
        self,
        spectrum_command: int,
        length: SpectrumIntLengths = SpectrumIntLengths.THIRTY_TWO,
    ) -> List[int]:
        param_values_each_device = []
        for device in self._devices:
            param_values_each_device.append(device.get_spectrum_api_param(spectrum_command, length))
        return param_values_each_device


def are_all_values_equal(values: List[int]) -> bool:
    return len(set(values)) == 1


def check_settings_constant_across_devices(values: List[int], setting_name: str) -> int:
    if are_all_values_equal(values):
        return values[0]
    else:
        raise SpectrumSettingsMismatchError(f"Devices have different {setting_name} settings")


def spectrum_netbox_factory(ip_address: str) -> SpectrumNetbox:
    devices = [
        networked_spectrum_device_factory(ip_address, 0),
        networked_spectrum_device_factory(ip_address, 1),
    ]
    return SpectrumNetbox(devices)
