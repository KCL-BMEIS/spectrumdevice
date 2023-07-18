"""Defines an error handling wrapper function for wrapping calls to the Spectrum API."""

# Christian Baker, King's College London
# Copyright (c) 2021 School of Biomedical Engineering & Imaging Sciences, King's College London
# Licensed under the MIT. You may obtain a copy at https://opensource.org/licenses/MIT.

import logging
from functools import wraps
from typing import Callable, Dict, Any

from pkg_resources import resource_filename

from spectrumdevice.exceptions import SpectrumApiCallFailed, SpectrumFIFOModeHardwareBufferOverrun
from spectrum_gmbh.spcerr import (
    ERR_OK,
    ERR_LASTERR,
    ERR_TIMEOUT,
    ERR_ABORT,
    ERR_FIFOHWOVERRUN,
)

logger = logging.getLogger(__name__)


def _parse_errors_table() -> Dict[int, str]:
    errors: Dict[int, str] = {}
    with open(resource_filename(__name__, "spectrum_errors.csv"), "r") as f:
        for line in f.readlines():
            cells = line.split(",")
            errors[int(cells[2].strip())] = cells[3].strip()
    return errors


KNOWN_ERRORS_WITH_DESCRIPTIONS = _parse_errors_table()
ERROR_CODES_TO_IGNORE = [ERR_OK]
ERROR_CODES_TO_REPORT_BUT_NOT_RAISE = [ERR_LASTERR, ERR_TIMEOUT, ERR_ABORT]
ERROR_CODES_WITH_EXCEPTIONS = {ERR_FIFOHWOVERRUN: SpectrumFIFOModeHardwareBufferOverrun}


def error_handler(func: Callable) -> Callable:
    """Used to wrap calls to the Spectrum API and handle the error codes generated by the hardware."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        error_code = func(*args, **kwargs)
        description = (
            KNOWN_ERRORS_WITH_DESCRIPTIONS[error_code]
            if error_code in KNOWN_ERRORS_WITH_DESCRIPTIONS
            else f"command or value {args[1]}."
        )

        if error_code in ERROR_CODES_TO_IGNORE:
            pass
        elif error_code in ERROR_CODES_TO_REPORT_BUT_NOT_RAISE:
            logger.warning(f"Unraised spectrum error from {func.__name__}: {description} " f"({error_code})")
        elif error_code in ERROR_CODES_WITH_EXCEPTIONS:
            raise ERROR_CODES_WITH_EXCEPTIONS[error_code](func.__name__, error_code, description)
        else:
            raise SpectrumApiCallFailed(func.__name__, error_code, description)

    return wrapper