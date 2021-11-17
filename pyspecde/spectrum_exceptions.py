class SpectrumIOError(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Spectrum IO error: {msg}")


class SpectrumSettingsMismatchError(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Spectrum Settings mismatch error: {msg}")


class SpectrumDeviceNotConnected(IOError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Spectrum device not connected: {msg}")
