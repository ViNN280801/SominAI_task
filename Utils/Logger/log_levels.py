import logging
from enum import Enum


class LogLevel(Enum):
    """
    Enumeration for log levels.

    This enumeration maps Python's logging levels to a more structured format.
    It can be used to specify logging verbosity in applications.

    Attributes:
        INFO: Informational messages.
        DEBUG: Debugging messages.
        WARNING: Warning messages indicating potential issues.
        ERROR: Error messages for failures that require attention.
        CRITICAL: Critical error messages for severe failures.
    """

    INFO = logging.INFO
    DEBUG = logging.DEBUG
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
