"""Defines exceptions raised by spectrumdevice device classes."""
from typing import Optional

from spectrumdevice.settings.card_dependent_properties import CARD_TYPE_DESCRIPTIONS, CardType


# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.


class SpectrumIOError(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Spectrum IO error: {msg}")


class SpectrumSettingsMismatchError(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Spectrum Settings mismatch error: {msg}")


class SpectrumDeviceNotConnected(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Spectrum device not connected: {msg}")


class SpectrumExternalTriggerNotEnabled(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"No external trigger is currently enabled: {msg}")


class SpectrumNoTransferBufferDefined(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"No transfer buffer has been defined: {msg}")


class SpectrumTriggerOperationNotImplemented(NotImplementedError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Operation is not implemented for the requested trigger channel: {msg}")


class SpectrumInvalidNumberOfEnabledChannels(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Invalid number of channels. Only 1, 2, 4 or 8 channels can be enabled: {msg}")


class SpectrumApiCallFailed(IOError):
    def __init__(
        self,
        call_description: str,
        error_code: Optional[int] = None,
        message: str = "Unknown",
    ) -> None:
        code_suffix = ({self.error_code_string(error_code)}) if error_code is not None else ""
        super().__init__(f'"{call_description}" failed with "{message}" {code_suffix}')

    @classmethod
    def error_code_string(cls, error_code: int) -> str:
        return f"Spectrum API error code: 0x{error_code:08x}"


class SpectrumFIFOModeHardwareBufferOverrun(SpectrumApiCallFailed):
    pass


class SpectrumFeatureNotSupportedByCard(SpectrumApiCallFailed):
    pass


class SpectrumParameterValueOutOfRange(SpectrumApiCallFailed):
    pass


class SpectrumWrongAcquisitionMode(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Incorrect acquisition mode: {msg}")


class SpectrumDriversNotFound(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Spectrum drivers not found: {msg}")


class SpectrumNotEnoughRoomInTimestampsBufferError(IOError):
    pass


class SpectrumNoTimestampsAvailableError(IOError):
    pass


class SpectrumTimestampsPollingTimeout(IOError):
    pass


class SpectrumWrongCardType(IOError):
    def __init__(self, detected_card_type: CardType) -> None:
        super().__init__(
            f"The connected card is a(n) {detected_card_type.name} ({CARD_TYPE_DESCRIPTIONS[detected_card_type]})."
        )


class SpectrumCardIsNotADigitiser(SpectrumWrongCardType):
    pass


class SpectrumCardIsNotAnAWG(SpectrumWrongCardType):
    pass


class SpectrumInvalidParameterValue(ValueError):
    def __init__(
        self, param_name: str, requested_value: float, param_min: float, param_max: float, param_step: float
    ) -> None:
        super().__init__(
            f"The requested {param_name} value of {requested_value} is invalid. At the current sample rate, it must be"
            f" between {param_min} and {param_max} inclusive, and a multiple of {param_step}."
        )


class MockRegisterNotImplemented(ValueError):
    pass
