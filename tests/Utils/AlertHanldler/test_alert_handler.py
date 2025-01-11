import pytest
from os import getenv
from unittest.mock import patch
from Utils.AlertHandler import AlertHandler, AlertDestination

__KBOT_TOKEN = getenv("__KBOT_TOKEN", "")
__KCHAT_ID = getenv("__KCHAT_ID", "")


@pytest.fixture
def mock_config():
    return {"telegram": {"bot_token": __KBOT_TOKEN, "chat_id": __KCHAT_ID}}


@pytest.fixture
def alert_handler(mock_config):
    return AlertHandler.get_instance(mock_config)


@patch("requests.post")
def test_send_alert_telegram_success(mock_post, alert_handler):
    """Test sending a message to Telegram successfully."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.text = '{"ok":true}'

    alert_handler.send_alert(AlertDestination.TELEGRAM, "Test message")

    mock_post.assert_called_once_with(
        f"https://api.telegram.org/bot{__KBOT_TOKEN}/sendMessage",
        data={"chat_id": __KCHAT_ID, "text": "Test message"},
    )


@patch("requests.post")
def test_send_alert_telegram_failure(mock_post, alert_handler):
    """Test handling failure while sending a message to Telegram."""
    mock_post.side_effect = Exception("Telegram API failed")

    with patch.object(alert_handler.logger, "log_error") as mock_log_error:
        alert_handler.send_alert(AlertDestination.TELEGRAM, "Test message")

        mock_log_error.assert_called_with(
            "Failed to send message to Telegram: Telegram API failed"
        )


@patch("Utils.AlertHandler.AlertHandler._send_to_monitoring")
def test_monitor_services(mock_send_to_monitoring, alert_handler):
    """Test monitoring services and sending alerts."""
    mock_send_to_monitoring.return_value = None

    services_state = {
        "service_a": "ok",
        "service_b": "error: database connection lost",
        "service_c": "ok",
    }

    with patch.object(alert_handler, "send_alert") as mock_send_alert:
        alert_handler.monitor_services(services_state)

        mock_send_alert.assert_any_call(
            AlertDestination.TELEGRAM,
            "Service service_b encountered an error: database connection lost.",
        )
        mock_send_alert.assert_any_call(
            AlertDestination.LOGGING,
            "Service service_b encountered an error: database connection lost.",
        )
        mock_send_alert.assert_any_call(
            AlertDestination.MONITORING,
            "Service service_b encountered an error: database connection lost.",
        )
        assert mock_send_alert.call_count == 3


def test_monitor_services_with_real_send(alert_handler):
    """Test monitoring services and sending real alerts with multiple services."""
    # Simulate services with states, including multiple errors with specific reasons
    services_state = {
        "service_1": "ok",
        "service_2": "ok",
        "service_3": "error: database connection lost",
        "service_4": "ok",
        "service_5": "ok",
        "service_6": "error: timeout occurred",
        "service_7": "ok",
        "service_8": "ok",
        "service_9": "ok",
        "service_10": "error: out of memory",
        "service_11": "ok",
        "service_12": "ok",
        "service_13": "ok",
        "service_14": "ok",
        "service_15": "ok",
        "service_16": "ok",
        "service_17": "ok",
        "service_18": "ok",
        "service_19": "ok",
        "service_20": "ok",
    }

    with patch.object(alert_handler.logger, "log_info") as mock_log_info:
        alert_handler.monitor_services(services_state)

        # Verify that logs contain alerts for services with errors
        mock_log_info.assert_any_call(
            "Sending message to Telegram: Service service_3 encountered an error: database connection lost."
        )
        mock_log_info.assert_any_call(
            "ALERT: Service service_3 encountered an error: database connection lost."
        )

        mock_log_info.assert_any_call(
            "Sending message to Telegram: Service service_6 encountered an error: timeout occurred."
        )
        mock_log_info.assert_any_call(
            "ALERT: Service service_6 encountered an error: timeout occurred."
        )

        mock_log_info.assert_any_call(
            "Sending message to Telegram: Service service_10 encountered an error: out of memory."
        )
        mock_log_info.assert_any_call(
            "ALERT: Service service_10 encountered an error: out of memory."
        )

        # Ensure the correct number of logs are created
        assert mock_log_info.call_count >= 6


@patch("Utils.Logger.Logger.log_error")
def test_send_alert_invalid_destination(mock_log_error, alert_handler):
    """Test handling an invalid alert destination."""
    alert_handler.send_alert("INVALID", "Test message")

    mock_log_error.assert_called_once_with("Unsupported alert destination: INVALID")


@patch("requests.post")
def test_singleton_pattern(mock_post, mock_config):
    """Test that AlertHandler enforces the singleton pattern."""
    instance1 = AlertHandler.get_instance(mock_config)
    instance2 = AlertHandler.get_instance(mock_config)

    assert instance1 is instance2


if __name__ == "__main__":
    pytest.main()
