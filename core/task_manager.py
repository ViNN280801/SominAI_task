import uuid
from typing import cast
from utils.types import TaskData
from core.redis_manager import RedisManager
from core.rabbit_publisher import RabbitMQPublisher
from modules.logger import Logger, LogLevel


class TaskManagerError(Exception):
    """Base exception for TaskManager."""

    pass


class TaskNotFoundError(TaskManagerError):
    """Raised when a task is not found."""

    def __init__(self, task_id: str):
        super().__init__(f"Task {task_id} does not exist.")
        self.task_id = task_id


class InvalidTaskDataError(TaskManagerError):
    """Raised when task data is invalid."""

    def __init__(self, message: str):
        super().__init__(message)


class TaskManager:
    """
    Manages tasks, including creating, updating statuses, and storing results.

    This class interacts with Redis for status management and RabbitMQ for
    task queueing.
    """

    def __init__(self, redis_config_path: str, rabbit_config_path: str):
        """
        Initializes the TaskManager with dependencies.

        :param redis_config_path: Path to the Redis configuration file.
        :param rabbit_config_path: Path to the RabbitMQ configuration file.
        """
        self.redis_manager = RedisManager(redis_config_path)
        self.rabbit_publisher = RabbitMQPublisher(rabbit_config_path)

        self.logger = Logger
        self.logger.configure_logger(name="TaskManager", level=LogLevel.INFO)

    async def create_task(self, keyword: str) -> str:
        """
        Asynchronously creates a new task and adds it to the queue.

        :param keyword: Keyword to be used for crawling.
        :return: Unique task ID.
        """
        task_id = str(uuid.uuid4())
        task_data: TaskData = {
            "status": "in_progress",
            "keyword": keyword,
            "region": None,
            "result": None,
        }
        await self.redis_manager.set_status(task_id, task_data)
        await self.rabbit_publisher.send_task(task_id, keyword)
        self.logger.log_info(
            f"Task {task_id} created with keyword '{keyword}' and added to queue."
        )
        return task_id

    async def get_task_status(self, task_id: str) -> TaskData | None:
        """
        Retrieves the status of a task.

        :param task_id: Unique ID of the task.
        :return: Task status and details if found, otherwise None.
        """
        task_status = self.redis_manager.get_status(task_id)
        if not isinstance(task_status, dict):
            self.logger.log_warning(f"Task {task_id} not found or has invalid data.")
            return None

        if not self._is_valid_task_data(task_status):
            self.logger.log_error(f"Task {task_id} has invalid data.")
            raise InvalidTaskDataError(f"Task {task_id} contains invalid data format.")

        task_data = cast(TaskData, task_status)
        self.logger.log_debug(f"Retrieved status for task {task_id}: {task_data}")
        return task_data

    async def update_task_status(
        self, task_id: str, status: str, result: dict | None = None
    ):
        """
        Asynchronously updates the status and result of a task.

        :param task_id: Unique ID of the task.
        :param status: New status of the task (e.g., 'completed', 'failed').
        :param result: Result of the task (optional).
        """
        task_status = await self.get_task_status(task_id)
        if task_status is None:
            self.logger.log_error(
                f"Cannot update status for non-existent task {task_id}."
            )
            raise TaskNotFoundError(f"Task {task_id} does not exist.")

        if not isinstance(result, (dict, type(None))):
            self.logger.log_error(
                f"Invalid result type for task {task_id}: {type(result)}."
            )
            raise InvalidTaskDataError(
                f"Result for task {task_id} must be a dictionary or None."
            )

        task_data: TaskData = {
            "status": status,
            "keyword": task_status["keyword"],
            "region": None,
            "result": result,
        }
        await self.redis_manager.set_status(task_id, task_data)
        self.logger.log_info(f"Task {task_id} updated to status '{status}'.")

    def _is_valid_task_data(self, data: TaskData | dict) -> bool:
        """
        Validates the structure of task data.

        :param data: Data to validate.
        :return: True if valid, False otherwise.
        """
        required_keys = {"status", "keyword"}
        if not isinstance(data, dict):
            return False

        # Check required keys
        if not required_keys.issubset(data.keys()):
            return False

        # Validate types of each field
        if not isinstance(data["status"], str):
            return False
        if not isinstance(data["keyword"], str):
            return False
        if "result" in data and not (
            data["result"] is None or isinstance(data["result"], dict)
        ):
            return False

        return True
