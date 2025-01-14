import os
import pytest
from modules.logger import LogLevelValidationError, LoggerConfigError, Logger, LogLevel
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reset_logger():
    # Before each test:
    Logger._logger = None
    Logger._log_file = None
    yield


@pytest.fixture
def mock_yaml_config():
    """Mock YAML configuration as a dictionary."""
    return {
        "version": 1,
        "handlers": {
            "console": {"class": "logging.StreamHandler", "level": "DEBUG"},
        },
        "root": {"handlers": ["console"], "level": "DEBUG"},
    }


@pytest.fixture
def configure_logger(mock_yaml_config):
    """Fixture to configure the logger with a dictionary configuration."""
    Logger.configure_logger(name="TestLogger", config_path=mock_yaml_config)
    yield
    Logger._logger = None  # Reset logger


@pytest.fixture
def configure_logger_with_dict(mock_yaml_config):
    """
    Another fixture specifically named for the test_log_info_message test,
    which references configure_logger_with_dict.
    """
    Logger.configure_logger(name="TestLogger", config_path=mock_yaml_config)
    yield
    Logger._logger = None


def test_configure_logger_with_dict(mock_yaml_config):
    """Test configuring the logger with a dictionary."""
    Logger.configure_logger(name="TestLogger", config_path=mock_yaml_config)
    assert Logger._logger is not None


def test_invalid_config_path():
    """Test configure_logger with an invalid config_path."""
    with pytest.raises(LoggerConfigError, match="Invalid config_path"):
        Logger.configure_logger(name="TestLogger", config_path={"invalid": "data"})


def test_log_info_with_valid_message(configure_logger):
    """Test log_info logs a valid informational message."""
    with patch("logging.Logger.info") as mock_info:
        Logger.log("This is an informational message.", LogLevel.INFO)
        mock_info.assert_called_once_with("This is an informational message.")


def test_log_info_without_configuring_logger():
    """Test log_info when logger is not configured."""
    with patch("logging.Logger.info") as mock_info:
        Logger.log("This should not log.", LogLevel.INFO)
        mock_info.assert_not_called()


def test_log_info_message(configure_logger_with_dict):
    """Test logging an informational message with fixture named configure_logger_with_dict."""
    with patch("logging.Logger.info") as mock_info:
        Logger.log_info("This is a test message.")
        mock_info.assert_called_once_with("This is a test message.")


def test_log_info_with_empty_message(configure_logger):
    """Test log_info with an empty message."""
    with patch("logging.Logger.info") as mock_info:
        Logger.log("", LogLevel.INFO)
        mock_info.assert_called_once_with("")


def test_log_info_with_large_message(configure_logger):
    """Test log_info with a very large message."""
    large_message = "A" * 10**6
    with patch("logging.Logger.info") as mock_info:
        Logger.log(large_message, LogLevel.INFO)
        mock_info.assert_called_once_with(large_message)


def test_log_info_with_non_string_message(configure_logger):
    """Test log_info with a non-string message."""
    with patch("logging.Logger.info") as mock_info:
        # Implicit string conversion expected
        Logger.log_info(12345)  # type: ignore
        mock_info.assert_called_once_with("12345")


def test_log_error_with_valid_message(configure_logger):
    """Test log_error logs a valid error message."""
    with patch("logging.Logger.error") as mock_error:
        Logger.log_error("This is an error message.")
        mock_error.assert_called_once_with("This is an error message.")


def test_log_error_without_configuring_logger():
    """Test log_error when logger is not configured."""
    with patch("logging.Logger.error") as mock_error:
        Logger.log("This should not log.", LogLevel.ERROR)
        mock_error.assert_not_called()


def test_log_error_with_empty_message(configure_logger):
    """Test log_error with an empty message."""
    with patch("logging.Logger.error") as mock_error:
        Logger.log("", LogLevel.ERROR)
        mock_error.assert_called_once_with("")


def test_log_error_with_large_message(configure_logger):
    """Test log_error with a very large message."""
    large_message = "E" * 10**6
    with patch("logging.Logger.error") as mock_error:
        Logger.log_error(large_message)
        mock_error.assert_called_once_with(large_message)


def test_log_error_with_non_string_message(configure_logger):
    """Test log_error with a non-string message."""
    with patch("logging.Logger.error") as mock_error:
        # Implicit string conversion expected
        Logger.log(3.14159, LogLevel.ERROR)  # type: ignore
        mock_error.assert_called_once_with("3.14159")


def test_configure_logger_with_invalid_level():
    """Test logger configuration with an invalid log level."""
    with pytest.raises(
        LogLevelValidationError, match="Invalid log level: INVALID_LEVEL"
    ):
        Logger.configure_logger(
            name="InvalidLevelLogger", log_file="invalid.log", level="INVALID_LEVEL"  # type: ignore
        )


def test_log_info_with_none_message(configure_logger):
    """Test log_info with a None message."""
    with patch("logging.Logger.info") as mock_info:
        Logger.log(None, LogLevel.INFO)  # type: ignore
        mock_info.assert_called_once_with("None")


def test_log_error_with_exception_message(configure_logger):
    """Test log_error logs exception message."""
    with patch("logging.Logger.error") as mock_error:
        try:
            raise ValueError("This is a test exception")
        except ValueError as e:
            Logger.log(str(e), LogLevel.ERROR)
        mock_error.assert_called_once_with("This is a test exception")


def test_configure_logger_with_nonexistent_file_path():
    """
    Test logger configuration with a non-writable log file path.

    If we pass config_path=invalid_path, the code interprets that as a config file path
    (which doesn't exist) and raises LoggerConfigError. Instead, we want a PermissionError
    for a non-writable file, so pass log_file=invalid_path instead.
    """
    invalid_path = "/nonexistent/path/test.log"
    with pytest.raises(PermissionError):
        Logger.configure_logger(
            name="TestLogger", log_file=invalid_path, level=LogLevel.DEBUG
        )


def test_log_to_unconfigured_logger():
    """Test logging to an unconfigured logger."""
    Logger._logger = None  # Ensure logger is unconfigured
    with patch("logging.Logger.info") as mock_info:
        Logger.log("This log should not occur.", LogLevel.ERROR)
        mock_info.assert_not_called()


def test_log_error_with_huge_message(configure_logger):
    """Test log_error with an excessively large message."""
    huge_message = "X" * 10**9  # 1 billion characters
    with patch("logging.Logger.error") as mock_error:
        Logger.log(huge_message, LogLevel.ERROR)
        mock_error.assert_called_once_with(huge_message)


def test_log_with_incorrect_method_call():
    """Test calling a non-existent logging method."""
    with pytest.raises(AttributeError):
        Logger.log_invalid_attibute("This method does not exist")  # type: ignore


def test_log_with_binary_message(configure_logger):
    """Test logging with binary data as the message."""
    binary_message = b"This is binary data"
    with patch("logging.Logger.info") as mock_info:
        # Convert binary to string
        Logger.log_info(binary_message.decode())
        mock_info.assert_called_once_with("This is binary data")


def test_logger_creates_log_directory():
    """Test that logger creates log/ directory if no specific log file is provided."""
    log_dir = "log"

    if os.path.exists(log_dir):
        for file in os.listdir(log_dir):
            os.remove(os.path.join(log_dir, file))
        os.rmdir(log_dir)

    Logger.configure_logger(name="TestLogger")
    assert os.path.exists(log_dir) and os.path.isdir(
        log_dir
    ), "log/ directory was not created."

    for file in os.listdir(log_dir):
        os.remove(os.path.join(log_dir, file))
    os.rmdir(log_dir)


def test_logger_log_directory_not_empty():
    """
    Test that logger creates a log file in log/ directory when no specific log file
    is provided. We also emit at least one message to ensure the file is written.
    """
    log_dir = "log"

    if os.path.exists(log_dir):
        for file in os.listdir(log_dir):
            os.remove(os.path.join(log_dir, file))
        os.rmdir(log_dir)

    Logger.configure_logger(name="TestLogger")

    # Force a log message so that the file definitely gets created/written
    Logger.log_info("Ensuring file is actually created.")

    assert os.path.exists(log_dir) and os.path.isdir(
        log_dir
    ), "log/ directory was not created."
    assert (
        len(os.listdir(log_dir)) > 0
    ), "log/ directory is empty, log file was not created."

    for file in os.listdir(log_dir):
        os.remove(os.path.join(log_dir, file))
    os.rmdir(log_dir)


if __name__ == "__main__":
    pytest.main()
