from enum import Enum


class AlertDestination(Enum):
    MONITORING = "monitoring"
    TELEGRAM = "telegram"
    LOGGING = "logging"
