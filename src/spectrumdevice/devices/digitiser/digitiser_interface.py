"""Defines public interfaces for controlling Spectrum digitiser devices and their channels."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from numpy import float_, ndarray
from numpy.typing import NDArray

from spectrumdevice.devices.abstract_device import SpectrumChannelInterface, SpectrumDeviceInterface
from spectrumdevice.settings import AcquisitionMode, AcquisitionSettings
from spectrumdevice import Measurement
from spectrumdevice.settings.channel import InputImpedance, InputCoupling, InputPath


class SpectrumDigitiserChannelInterface(SpectrumChannelInterface, ABC):
    """Defines the public interface for control of the channels of Spectrum digitiser device. All properties are read-
    only and must be set with their respective setter methods."""

    @property
    @abstractmethod
    def vertical_range_in_mv(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_vertical_range_in_mv(self, vertical_range: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def vertical_offset_in_percent(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_vertical_offset_in_percent(self, offset: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def convert_raw_waveform_to_voltage_waveform(self, raw_waveform: ndarray) -> ndarray:
        raise NotImplementedError()

    @property
    @abstractmethod
    def input_impedance(self) -> InputImpedance:
        raise NotImplementedError()

    @abstractmethod
    def set_input_impedance(self, input_impedance: InputImpedance) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def input_coupling(self) -> InputCoupling:
        raise NotImplementedError()

    @abstractmethod
    def set_input_coupling(self, input_coupling: InputCoupling) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def input_path(self) -> InputPath:
        raise NotImplementedError()

    @abstractmethod
    def set_input_path(self, input_path: InputPath) -> None:
        raise NotImplementedError()


class SpectrumDigitiserInterface(SpectrumDeviceInterface, ABC):
    """Defines the public interface for control of all Spectrum digitiser devices, be they StarHub composite devices
    (e.g. the NetBox) or individual digitiser cards. All properties are read-only and must be set with their respective
    setter methods."""

    @abstractmethod
    def wait_for_acquisition_to_complete(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def configure_acquisition(self, settings: AcquisitionSettings) -> None:
        raise NotImplementedError()

    @abstractmethod
    def execute_standard_single_acquisition(self) -> Measurement:
        raise NotImplementedError()

    @abstractmethod
    def execute_finite_fifo_acquisition(self, num_measurements: int) -> List[Measurement]:
        raise NotImplementedError()

    @abstractmethod
    def execute_continuous_fifo_acquisition(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_waveforms(self) -> List[List[NDArray[float_]]]:
        raise NotImplementedError()

    @abstractmethod
    def get_timestamp(self) -> Optional[datetime]:
        raise NotImplementedError()

    @abstractmethod
    def enable_timestamping(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def acquisition_length_in_samples(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_acquisition_length_in_samples(self, length_in_samples: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def post_trigger_length_in_samples(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_post_trigger_length_in_samples(self, length_in_samples: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def acquisition_mode(self) -> AcquisitionMode:
        raise NotImplementedError()

    @abstractmethod
    def set_acquisition_mode(self, mode: AcquisitionMode) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def batch_size(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_batch_size(self, batch_size: int) -> None:
        raise NotImplementedError()
