from enum import Enum


class AlertDestination(Enum):
    """
    Enumeration for alert destinations.

    This enumeration defines different destinations where alerts can be sent.
    It provides flexibility for handling and routing alerts in various systems.

    Attributes:
        MONITORING: Destination for monitoring systems (e.g., dashboards or monitoring tools).
        TELEGRAM: Destination for sending alerts to Telegram.
        LOGGING: Destination for logging alerts into application logs.
    """

    MONITORING = "monitoring"
    TELEGRAM = "telegram"
    LOGGING = "logging"
