"""Defines public interfaces for controlling Spectrum digitiser devices and their channels."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Tuple, Sequence

from numpy import ndarray, float_
from numpy.typing import NDArray

from spectrumdevice.devices.measurement import Measurement
from spectrumdevice.settings import TriggerSettings, AcquisitionSettings
from spectrumdevice.settings import SpectrumRegisterLength
from spectrumdevice.settings.device_modes import AcquisitionMode, ClockMode
from spectrumdevice.settings.status import CARD_STATUS_TYPE, STAR_HUB_STATUS_TYPE
from spectrumdevice.settings.channel import SpectrumChannelName
from spectrumdevice.settings.io_lines import AvailableIOModes
from spectrumdevice.settings.triggering import TriggerSource, ExternalTriggerMode
from spectrumdevice.settings.card_features import CardFeature, AdvancedCardFeature
from spectrumdevice.settings.transfer_buffer import TransferBuffer, CardToPCDataTransferBuffer


class SpectrumChannelInterface(ABC):
    """Defines the public interface for control of the channels of Spectrum digitiser device. All properties are read-
    only and must be set with their respective setter methods."""

    @property
    @abstractmethod
    def name(self) -> SpectrumChannelName:
        raise NotImplementedError

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


class SpectrumDeviceInterface(ABC):
    """Defines the public interface for control of all Spectrum digitiser devices, be they StarHub composite devices
    (e.g. the NetBox) or individual digitiser cards. All properties are read-only and must be set with their respective
    setter methods."""

    @property
    @abstractmethod
    def connected(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def reconnect(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError()

    @property
    def status(self) -> Union[CARD_STATUS_TYPE, STAR_HUB_STATUS_TYPE]:
        raise NotImplementedError()

    @abstractmethod
    def start_acquisition(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def stop_acquisition(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def wait_for_acquisition_to_complete(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def start_transfer(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def stop_transfer(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def wait_for_transfer_to_complete(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def configure_acquisition(self, settings: AcquisitionSettings) -> None:
        raise NotImplementedError()

    @abstractmethod
    def execute_standard_single_acquisition(self) -> Measurement:
        raise NotImplementedError()

    @abstractmethod
    def execute_finite_multi_fifo_acquisition(self, num_iterations: int) -> List[Measurement]:
        raise NotImplementedError()

    @abstractmethod
    def execute_continuous_multi_fifo_acquisition(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def transfer_buffers(self) -> List[TransferBuffer]:
        raise NotImplementedError()

    @abstractmethod
    def define_transfer_buffer(self, buffer: Optional[List[CardToPCDataTransferBuffer]] = None) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_waveforms(self) -> List[NDArray[float_]]:
        raise NotImplementedError()

    @abstractmethod
    def get_timestamp(self) -> Optional[datetime]:
        raise NotImplementedError()

    @abstractmethod
    def enable_timestamping(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def channels(self) -> Sequence[SpectrumChannelInterface]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def enabled_channels(self) -> List[int]:
        raise NotImplementedError()

    @abstractmethod
    def set_enabled_channels(self, channels_nums: List[int]) -> None:
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
    def timeout_in_ms(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_timeout_in_ms(self, timeout_in_ms: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def trigger_sources(self) -> List[TriggerSource]:
        raise NotImplementedError()

    @abstractmethod
    def set_trigger_sources(self, source: List[TriggerSource]) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def external_trigger_mode(self) -> ExternalTriggerMode:
        raise NotImplementedError()

    @abstractmethod
    def set_external_trigger_mode(self, mode: ExternalTriggerMode) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def external_trigger_level_in_mv(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_external_trigger_level_in_mv(self, level: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def external_trigger_pulse_width_in_samples(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_external_trigger_pulse_width_in_samples(self, width: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def configure_trigger(self, settings: TriggerSettings) -> None:
        raise NotImplementedError()

    @abstractmethod
    def apply_channel_enabling(self) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def clock_mode(self) -> ClockMode:
        raise NotImplementedError()

    @abstractmethod
    def set_clock_mode(self, mode: ClockMode) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def sample_rate_in_hz(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def set_sample_rate_in_hz(self, rate: int) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def available_io_modes(self) -> AvailableIOModes:
        raise NotImplementedError()

    @property
    @abstractmethod
    def feature_list(self) -> List[Tuple[List[CardFeature], List[AdvancedCardFeature]]]:
        raise NotImplementedError()

    @abstractmethod
    def write_to_spectrum_device_register(
        self,
        spectrum_register: int,
        value: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def read_spectrum_device_register(
        self,
        spectrum_register: int,
        length: SpectrumRegisterLength = SpectrumRegisterLength.THIRTY_TWO,
    ) -> int:
        raise NotImplementedError()
