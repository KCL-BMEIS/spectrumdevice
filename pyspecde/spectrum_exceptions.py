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
