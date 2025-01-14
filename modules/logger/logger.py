import os
import logging
from logging.config import dictConfig
from modules.logger.log_levels import LogLevel, LogLevelValidationError
from configs.config_loader import (
    ConfigLoader,
    ConfigFileNotFoundError,
    ConfigFileFormatError,
)


class LoggerError(Exception):
    """Base exception for Logger errors."""

    pass


class LoggerConfigError(LoggerError):
    """Raised when there is an error in loading or applying the configuration."""

    pass


class LoggerFileError(LoggerError):
    """Raised when there is an issue with log file operations."""

    pass


class Logger:
    """
    A universal logger module that provides configurable logging capabilities.
    """

    _logger: logging.Logger | None = None
    _log_file: str | None = None

    @classmethod
    def _load_yaml_config(cls, config_path: str) -> dict:
        """
        Loads the YAML configuration file for logging using ConfigLoader.
        """
        try:
            return ConfigLoader.load_config(config_path)
        except (ConfigFileNotFoundError, ConfigFileFormatError) as e:
            # Re-raise as LoggerConfigError
            raise LoggerConfigError(f"Failed to load logging configuration: {e}") from e
        except Exception as e:
            raise LoggerConfigError(
                f"Unexpected error loading logging configuration: {e}"
            ) from e

    @classmethod
    def _ensure_log_directory(cls) -> None:
        """
        Ensures that the log directory exists. If it doesn't, creates it.
        """
        if cls._log_file:
            directory = os.path.dirname(cls._log_file) or "log"
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
            except PermissionError as e:
                # Re-raise as the same PermissionError to match tests expecting it
                raise PermissionError(
                    f"Cannot write to directory '{directory}': {e}"
                ) from e
            except Exception as e:
                # For any other error, raise LoggerFileError
                raise LoggerFileError(
                    f"Failed to create log directory '{directory}': {e}"
                ) from e

    @classmethod
    def _validate_log_level(cls, level: LogLevel) -> None:
        """
        Ensures the provided log level is valid.
        """
        if not isinstance(level, LogLevel):
            raise LogLevelValidationError(f"Invalid log level: {level}")

    @classmethod
    def _validate_message(cls, message) -> str:
        """
        Validates and converts the message to a string.
        """
        try:
            return str(message)
        except Exception as e:
            raise TypeError(f"Message cannot be converted to string: {message}") from e

    @classmethod
    def configure_logger(
        cls,
        name: str,
        config_path: dict | str | None = None,
        level: LogLevel = LogLevel.INFO,
        log_file: str | None = None,
    ) -> None:
        """
        Configures the logger using a YAML configuration file or defaults.

        :param name:        Name of the logger.
        :param config_path: Path/dict to the YAML configuration. If None, defaults are used.
        :param level:       Logging level if no config is provided.
        :param log_file:    File path for log output (optional).
        :raises LoggerConfigError: If the config fails to load or apply.
        """
        cls._validate_log_level(level)

        # If user explicitly passes a log_file, store it.
        if log_file is not None:
            cls._log_file = log_file

        if config_path:
            # If config_path is a dictionary
            if isinstance(config_path, dict):
                # Check if the dictionary has 'version' key
                if "version" not in config_path:
                    raise LoggerConfigError(
                        "Invalid config_path: 'version' key is missing."
                    )
                try:
                    dictConfig(config_path)
                    cls._logger = logging.getLogger(name)
                    return
                except Exception as e:
                    raise LoggerConfigError(
                        f"Failed to apply configuration from dict: {e}"
                    ) from e
            # If config_path is a file path
            elif os.path.exists(config_path):
                try:
                    config = cls._load_yaml_config(config_path)
                    if not config or "version" not in config:
                        raise LoggerConfigError(
                            "Invalid config_path: 'version' key is missing."
                        )

                    dictConfig(config)
                    cls._logger = logging.getLogger(name)
                    return
                except Exception as e:
                    raise LoggerConfigError(
                        f"Failed to load configuration from {config_path}: {e}"
                    ) from e
            else:
                # If config_path is neither a valid dict nor an existing file
                raise LoggerConfigError(f"Invalid config_path: {config_path}")

        # If no config_path was provided or it was None, use a default config
        # to ensure only ONE file is created, remove the timestamp approach:
        if cls._log_file is None:
            cls._log_file = os.path.join("log", "app.log")

        cls._ensure_log_directory()

        # Create file handler
        file_handler = logging.FileHandler(cls._log_file)
        file_handler.setLevel(level.value)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level.value)

        # Common formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        cls._logger = logging.getLogger(name)
        cls._logger.setLevel(level.value)
        cls._logger.addHandler(file_handler)
        cls._logger.addHandler(console_handler)

    @classmethod
    def log(cls, message, level: LogLevel) -> None:
        """
        Logs a message at the specified log level.
        """
        if cls._logger:
            # Convert message to str
            message_str = cls._validate_message(message)

            if level == LogLevel.INFO:
                cls._logger.info(message_str)
            elif level == LogLevel.DEBUG:
                cls._logger.debug(message_str)
            elif level == LogLevel.WARNING:
                cls._logger.warning(message_str)
            elif level == LogLevel.ERROR:
                cls._logger.error(message_str)
            elif level == LogLevel.CRITICAL:
                cls._logger.critical(message_str)

    @classmethod
    def log_info(cls, message) -> None:
        """Logs an informational message."""
        cls.log(message, LogLevel.INFO)

    @classmethod
    def log_debug(cls, message) -> None:
        """Logs a debug message."""
        cls.log(message, LogLevel.DEBUG)

    @classmethod
    def log_warning(cls, message) -> None:
        """Logs a warning message."""
        cls.log(message, LogLevel.WARNING)

    @classmethod
    def log_error(cls, message) -> None:
        """Logs an error message."""
        cls.log(message, LogLevel.ERROR)

    @classmethod
    def log_critical(cls, message) -> None:
        """Logs a critical message."""
        cls.log(message, LogLevel.CRITICAL)
