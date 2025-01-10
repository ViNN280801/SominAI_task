import os
import logging
from datetime import datetime
from Utils.Logger import LogLevel


class Logger:
    """
    A universal logger module that provides configurable logging capabilities.

    This class allows logging messages at different levels and integrates seamlessly
    into any system.
    """

    _logger: logging.Logger | None = None
    _log_file: str | None = None

    @classmethod
    def _ensure_log_directory(cls) -> None:
        """
        Ensures that the log directory exists. If it doesn't, creates it.
        """
        if cls._log_file:
            directory = os.path.dirname(cls._log_file) or "log"
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    @classmethod
    def _validate_log_level(cls, level: LogLevel) -> None:
        """
        Ensures the provided log level is valid.

        :param level: Log level to validate, must be an instance of LogLevel.
        :raises ValueError: If the log level is not a valid LogLevel.
        """
        if not isinstance(level, LogLevel):
            raise ValueError(f"Invalid log level: {level}")

    @classmethod
    def _validate_log_file(cls, log_file: str) -> None:
        """
        Validates the log file path to ensure it is writable and valid.

        :param log_file: Path to the log file.
        :raises FileNotFoundError: If the directory for the log file does not exist.
        :raises IsADirectoryError: If the log file path points to a directory.
        :raises PermissionError: If the log file cannot be written to.
        """
        # Generate default log file name if not provided
        if log_file is None:
            log_dir = "log"
            timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            log_file = os.path.join(log_dir, f"{timestamp}.log")

        directory = os.path.dirname(log_file) or "log"

        # Ensure directory exists or create it
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Ensure the path is not a directory
        if os.path.isdir(log_file):
            raise IsADirectoryError(
                f"Path points to a directory, not a file: {log_file}")

        # Ensure the directory is writable
        if not os.access(directory, os.W_OK):
            raise PermissionError(f"Cannot write to directory: {directory}")

        # Ensure log directory exists
        cls._ensure_log_directory()

    @classmethod
    def _validate_message(cls, message) -> str:
        """
        Validates and converts the message to a string.

        :param message: The message to validate.
        :return: The validated message as a string.
        :raises TypeError: If the message cannot be converted to a string.
        """
        try:
            return str(message)
        except Exception as e:
            raise TypeError(f"Message cannot be converted to string: {
                            message}") from e

    @classmethod
    def configure_logger(cls, name: str, log_file: str | None = None, level: LogLevel = LogLevel.INFO) -> None:
        """
        Configures the logger with a specific name, log file, and logging level.

        :param name: Name of the logger.
        :param log_file: Path to the log file. If None, a default file in the 'log/' directory is created.
        :param level: Logging level from LogLevel enum.
        """
        # Generating filename if it doesn't specified
        if log_file is None:
            log_dir = "log"
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            log_file = os.path.join(log_dir, f"{timestamp}.log")

        cls._log_file = log_file
        cls._validate_log_file(log_file)
        cls._validate_log_level(level)

        cls._logger = logging.getLogger(name)
        cls._logger.setLevel(level.value)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level.value)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level.value)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Adding handlers
        cls._logger.addHandler(file_handler)
        cls._logger.addHandler(console_handler)

    @classmethod
    def log(cls, message: str, level: LogLevel) -> None:
        """
        Logs a message at the specified log level.

        :param message: The message to log.
        :param level: The log level from LogLevel enum.
        """
        if cls._logger:
            cls._ensure_log_directory()  # Ensure log directory exists
            validated_message = cls._validate_message(message)

            # Log based on the level
            if level == LogLevel.INFO:
                cls._logger.info(validated_message)
            elif level == LogLevel.DEBUG:
                cls._logger.debug(validated_message)
            elif level == LogLevel.WARNING:
                cls._logger.warning(validated_message)
            elif level == LogLevel.ERROR:
                cls._logger.error(validated_message)
            elif level == LogLevel.CRITICAL:
                cls._logger.critical(validated_message)

    @classmethod
    def log_info(cls, message: str) -> None:
        """
        Logs an informational message.

        :param message: The message to log.
        """
        cls.log(message, LogLevel.INFO)

    @classmethod
    def log_debug(cls, message: str) -> None:
        """
        Logs a debug message.

        :param message: The message to log.
        """
        cls.log(message, LogLevel.DEBUG)

    @classmethod
    def log_warning(cls, message: str) -> None:
        """
        Logs a warning message.

        :param message: The message to log.
        """
        cls.log(message, LogLevel.WARNING)

    @classmethod
    def log_error(cls, message: str) -> None:
        """
        Logs an error message.

        :param message: The message to log.
        """
        cls.log(message, LogLevel.ERROR)

    @classmethod
    def log_critical(cls, message: str) -> None:
        """
        Logs a critical message.

        :param message: The message to log.
        """
        cls.log(message, LogLevel.CRITICAL)
