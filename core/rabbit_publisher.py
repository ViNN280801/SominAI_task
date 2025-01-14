import json
import aio_pika
from configs.config_loader import ConfigLoader
from modules.logger import Logger, LogLevel
from modules.exception_handler import ExceptionHandler


class RabbitMQPublisherError(Exception):
    """Base exception for RabbitMQPublisher."""


class RabbitMQConnectionError(RabbitMQPublisherError):
    """Raised when there is a connection error."""


class RabbitMQMessageError(RabbitMQPublisherError):
    """Raised when there is an error publishing a message."""


class RabbitMQPublisher:
    """
    Handles asynchronous communication with RabbitMQ for task publishing.
    """

    def __init__(self, config_path: str = "configs/rabbitmq.yaml"):
        """
        Initializes the RabbitMQPublisher with configuration from a file.

        :param config_path: Path to the RabbitMQ configuration file.
        """
        config = ConfigLoader.load_config(config_path).get("rabbitmq", {})
        self.host = config.get("host", "localhost")
        self.queue = config.get("queue", "task_queue")
        self.username = config.get("username", "guest")
        self.password = config.get("password", "guest")

        self.logger = Logger
        self.logger.configure_logger(name="RabbitMQPublisher", level=LogLevel.INFO)
        self.exception_handler = ExceptionHandler()

    async def _ensure_channel_initialized(self) -> None:
        """
        Check whether the RabbitMQ channel is initialized or not.

        :raise RabbitMQConnectionError: In case if channel is 'None'.
        """
        if not hasattr(self, "channel") or not self.channel:
            await self.connect()

    async def connect(self):
        """
        Asynchronously connects to RabbitMQ and declares the default queue.
        """
        try:
            self.connection = await aio_pika.connect_robust(
                f"amqp://{self.username}:{self.password}@{self.host}/"
            )
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(self.queue, durable=True)
            self.logger.log_info(
                f"Connected to RabbitMQ at {self.host}, queue '{self.queue}' initialized."
            )
        except Exception as e:
            self.logger.log_error(f"Failed to connect to RabbitMQ: {e}")
            raise RabbitMQConnectionError("Could not connect to RabbitMQ.") from e

    async def send_task(self, task_id: str, keyword: str) -> None:
        """
        Publishes a task message to the RabbitMQ queue asynchronously.

        :param task_id: Unique ID of the task.
        :param keyword: Keyword for the task.
        """
        try:
            await self._ensure_channel_initialized()
            message = {"task_id": task_id, "keyword": keyword}
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=self.queue,
            )
            self.logger.log_info(
                f"Task {task_id} with keyword '{keyword}' sent to queue '{self.queue}'."
            )
        except Exception as e:
            self.logger.log_error(f"Failed to send task {task_id} to RabbitMQ: {e}")
            self.exception_handler.handle_exception(
                e, {"task_id": task_id, "keyword": keyword}
            )
            raise RabbitMQMessageError(
                f"Error sending task {task_id} to RabbitMQ."
            ) from e

    async def publish(self, queue: str, message: dict) -> None:
        """
        Publishes a message to a specified RabbitMQ queue asynchronously.

        :param queue: The name of the queue.
        :param message: The message to publish (as a dictionary).
        """
        try:
            await self._ensure_channel_initialized()
            await self.channel.declare_queue(queue, durable=True)
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue,
            )
            self.logger.log_info(f"Message sent to queue '{queue}': {message}")
        except Exception as e:
            self.logger.log_error(f"Failed to publish message to RabbitMQ: {e}")
            self.exception_handler.handle_exception(
                e, {"queue": queue, "message": message}
            )
            raise RabbitMQMessageError("Error publishing message to RabbitMQ.") from e

    async def close_connection(self) -> None:
        """
        Asynchronously closes the connection to RabbitMQ.
        """
        try:
            if self.connection:
                await self.connection.close()
                self.logger.log_info("RabbitMQ connection closed.")
        except Exception as e:
            self.logger.log_error(f"Failed to close RabbitMQ connection: {e}")
            raise RabbitMQPublisherError("Error closing RabbitMQ connection.") from e
