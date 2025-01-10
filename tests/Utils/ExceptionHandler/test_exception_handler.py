#! python3.13

import os
import pytest
from unittest.mock import patch
from Utils.Logger import Logger, LogLevel
from Utils.ExceptionHandler import ExceptionHandler


def file_cleaner(filepath: str) -> None:
    if filepath and os.path.exists(filepath):
        os.remove(filepath)


def test_handle_exception_clean():
    """Test handling a standard exception with valid context."""
    exception = ValueError("This is a test exception.")
    context = {"path": "/test", "method": "GET"}

    with patch("Utils.Logger.Logger.log_error") as mock_log_error:
        response = ExceptionHandler.handle_exception(exception, context)

    mock_log_error.assert_called_once_with(
        f"Exception: ValueError. Message: {exception}. Context: {context}"
    )

    assert response == {
        "error": {
            "type": "ValueError",
            "message": "This is a test exception.",
            "context": context,
        }
    }


def test_handle_exception_with_none_context():
    """Test handling an exception with None as context."""
    exception = RuntimeError("Test exception with None context.")
    context = None

    with pytest.raises(TypeError, match="`context` must be a dictionary"):
        ExceptionHandler.handle_exception(exception, context)  # type: ignore


def test_handle_exception_with_large_context():
    """Test handling an exception with a very large context."""
    exception = RuntimeError("Test exception with large context.")
    context = {"path": "/large", "method": "GET", "data": "x" * 10**6}

    with patch("Utils.Logger.Logger.log_error") as mock_log_error:
        response = ExceptionHandler.handle_exception(exception, context)

    mock_log_error.assert_called_once()
    assert len(response["error"]["context"]["data"]) == 10**6


def test_handle_exception_with_non_dict_context():
    """Test handling an exception with a non-dictionary context."""
    exception = RuntimeError("Test exception with invalid context.")
    context = ["invalid", "context"]

    with pytest.raises(TypeError, match="`context` must be a dictionary"):
        ExceptionHandler.handle_exception(exception, context)  # type: ignore


def test_handle_exception_with_empty_exception_message():
    """Test handling an exception with an empty message."""
    exception = ValueError("")
    context = {"path": "/empty", "method": "GET"}

    with patch("Utils.Logger.Logger.log_error") as mock_log_error:
        response = ExceptionHandler.handle_exception(exception, context)

    mock_log_error.assert_called_once()
    assert response["error"]["message"] == ""


def test_handle_exception_with_many_exceptions():
    """Stress test handling a large number of exceptions."""
    context = {"path": "/stress", "method": "POST"}
    exceptions = [ValueError(f"Exception {i}") for i in range(1000)]

    with patch("Utils.Logger.Logger.log_error") as mock_log_error:
        for exception in exceptions:
            ExceptionHandler.handle_exception(exception, context)

    assert mock_log_error.call_count == 1000


def test_handle_exception_with_enormous_exceptions():
    """Stress test handling an exception with a enormous message."""
    exception = RuntimeError("x" * 10**9)
    context = {"path": "/enormous", "method": "PUT"}

    with patch("Utils.Logger.Logger.log_error") as mock_log_error:
        response = ExceptionHandler.handle_exception(exception, context)

    mock_log_error.assert_called_once()
    assert len(response["error"]["message"]) == 10**9


def test_handle_exception_logs_correctly():
    """Integration test to check Logger logs exceptions correctly."""
    exception = KeyError("Integration test exception.")
    context = {"path": "/integration", "method": "PATCH"}
    filepath = "integration.log"

    Logger.configure_logger(
        name="TestLogger", log_file=filepath, level=LogLevel.ERROR)

    with patch.object(Logger, "log_error") as mock_log_error:
        ExceptionHandler.handle_exception(exception, context)

    mock_log_error.assert_called_once_with(
        f"Exception: KeyError. Message: {exception}. Context: {context}"
    )

    file_cleaner(filepath)


def test_handle_exception_with_logger_file():
    """Integration test to check if logs are written to file."""
    exception = KeyError("Integration test to log into file.")
    context = {"path": "/file", "method": "DELETE"}
    filepath = "file_test.log"

    Logger.configure_logger(
        name="FileLogger", log_file=filepath, level=LogLevel.ERROR)
    ExceptionHandler.handle_exception(exception, context)

    with open(filepath, "r") as log_file:
        logs = log_file.read()

    expected_message = (
        "Exception: KeyError. Message: 'Integration test to log into file.'. "
        "Context: {'path': '/file', 'method': 'DELETE'}"
    )
    assert expected_message in logs, f"Expected message not found in logs: {
        logs}"

    file_cleaner(filepath)


def test_handle_exception_with_logger_levels():
    """Integration test to validate logging levels in Logger."""
    exception = RuntimeError("Logger level integration test.")
    context = {"path": "/levels", "method": "GET"}
    filepath = "level_test.log"

    Logger.configure_logger(
        name="LevelLogger", log_file=filepath, level=LogLevel.WARNING)

    with patch.object(Logger, "log_error") as mock_log_error:
        ExceptionHandler.handle_exception(exception, context)

    mock_log_error.assert_called_once()

    file_cleaner(filepath)


if __name__ == "__main__":
    pytest.main()
