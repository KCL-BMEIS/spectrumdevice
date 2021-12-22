import logging
from functools import wraps
from typing import Callable, Dict, Any

from pyspecde.spectrum_wrapper.exceptions import SpectrumApiCallFailed
from spectrum_gmbh.spcerr import (
    ERR_OK,
    ERR_LASTERR,
    ERR_TIMEOUT,
    ERR_ABORT,
    ERR_VALUE,
    ERR_INVALIDHANDLE,
    ERR_SETUP,
    ERR_RUNNING,
)

logger = logging.getLogger(__name__)


def error_handler(func: Callable) -> Callable:

    unreported_unraised_error_codes = {ERR_OK: "Execution OK, no error"}

    reported_unraised_error_codes: Dict[int, str] = {
        ERR_LASTERR: "Old error waiting to be read. Please read the full error information before proceeding. The "
        "driver is locked until the error information can be read.",
        ERR_TIMEOUT: "A timeout occurred while waiting for an interrupt.",
        ERR_ABORT: "Abort of wait function. The function has been aborted from another thread.",
    }

    known_raised_error_codes = {
        ERR_VALUE: "The value for this register is not in a valid range. The allowed values and ranges are listed in"
        "the board specific documentation.",
        ERR_INVALIDHANDLE: "The used handle is not valid.",
        ERR_SETUP: "The programmed setup for the card is not valid.",
        ERR_RUNNING: "The board is still running. this function is not available now or this register is not accessible"
        " now.",
    }

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        error_code = func(*args, **kwargs)
        if error_code in unreported_unraised_error_codes:
            pass
        elif error_code in reported_unraised_error_codes:
            logger.warning(
                f"Unraised spectrum error from {func.__name__}: {reported_unraised_error_codes[error_code]} "
                f"({error_code})"
            )
        elif error_code in known_raised_error_codes:
            raise SpectrumApiCallFailed(func.__name__, error_code, known_raised_error_codes[error_code])
        else:
            raise SpectrumApiCallFailed(func.__name__, error_code, f"command or value {args[1]}.")

    return wrapper
