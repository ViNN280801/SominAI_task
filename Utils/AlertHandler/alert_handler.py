import requests
from Utils.Logger import Logger, LogLevel
from Utils.AlertHandler import AlertDestination


class AlertHandler:
    """
    A universal alert handler that supports multiple notification channels.

    This handler initializes once and monitors the state of services. If a signal
    is detected from any service, it sends an alert to the specified destination.
    """

    _instance = None

    @staticmethod
    def get_instance(config: dict):
        """
        Returns the singleton instance of the AlertHandler.

        :param config: Configuration dictionary for notification channels.
        :return: The AlertHandler singleton instance.
        """
        if AlertHandler._instance is None:
            AlertHandler._instance = AlertHandler(config)
        return AlertHandler._instance

    def __init__(self, config: dict):
        """
        Initializes the alert handler.

        :param config: Configuration dictionary for notification channels.
        """
        if AlertHandler._instance is not None:
            raise Exception("This class is a singleton! Use get_instance().")
        self.config = config
        self.logger = Logger
        self.logger.configure_logger(
            name="AlertHandler", level=LogLevel.INFO)

    def monitor_services(self, services: dict):
        """
        Monitors the state of services and triggers alerts if any service sends a signal.

        :param services: Dictionary of services and their states.
        """
        for service_name, state in services.items():
            if state.startswith("error"):
                # Extract reason if provided (e.g., "error: reason")
                reason = state.split(": ", 1)[
                    1] if ": " in state else "unspecified issue"
                message = f"Service {
                    service_name} encountered an error: {reason}."
                self.logger.log_info(
                    f"Sending alert [{message}] to all monitoring services"
                )
                self.send_alert(AlertDestination.TELEGRAM, message)
                self.send_alert(AlertDestination.LOGGING, message)
                self.send_alert(AlertDestination.MONITORING, message)

    def send_alert(self, destination: AlertDestination, message: str) -> None:
        """
        Sends an alert to the specified destination.

        :param destination: Alert destination from AlertDestination enum.
        :param message: Message text to be sent.
        """
        if destination == AlertDestination.MONITORING:
            self._send_to_monitoring(message)
        elif destination == AlertDestination.TELEGRAM:
            self._send_to_telegram(message)
        elif destination == AlertDestination.LOGGING:
            self._log_alert(message)
        else:
            self.logger.log_error(
                f"Unsupported alert destination: {destination}")

    def _send_to_monitoring(self, message: str) -> None:
        """ Sending to monitoring services logic. """
        pass

    def _send_to_telegram(self, message: str) -> None:
        bot_token = self.config.get("telegram", {}).get("bot_token")
        chat_id = self.config.get("telegram", {}).get("chat_id")
        if not bot_token or not chat_id:
            self.logger.log_error(
                "Telegram bot token or chat ID not configured.")
            return
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message}
            self.logger.log_info(f"Sending message to Telegram: {message}")
            response = requests.post(url, data=payload)
            self.logger.log_info(f"Telegram response: {
                                 response.status_code} - {response.text}")
            response.raise_for_status()
        except Exception as e:
            self.logger.log_error(f"Failed to send message to Telegram: {e}")

    def _log_alert(self, message: str) -> None:
        self.logger.log_info(f"ALERT: {message}")
