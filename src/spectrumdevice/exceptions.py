"""Defines exceptions raised by spectrumdevice device classes."""

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
        error_code: int,
        message: str = "Unknown",
    ) -> None:
        super().__init__(f'"{call_description}" failed with "{message}" ({self.error_code_string(error_code)})')

    @classmethod
    def error_code_string(cls, error_code: int) -> str:
        return f"Spectrum API error code: 0x{error_code:08x}"


class SpectrumFIFOModeHardwareBufferOverrun(SpectrumApiCallFailed):
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
