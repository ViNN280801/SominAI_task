import json
import redis.asyncio as redis
from configs.config_loader import ConfigLoader
from utils.types import TaskData
from modules.logger import Logger, LogLevel
from modules.exception_handler import ExceptionHandler


class RedisManagerError(Exception):
    """Custom exception for RedisManager."""


class RedisManager:
    """
    Asynchronous manager for interactions with the Redis database for task status storage.
    """

    def __init__(self, config_path: str = "configs/config.yaml"):
        config = ConfigLoader.load_config(config_path).get("redis", {})
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 6379)
        self.db = config.get("db", 0)

        self.logger = Logger
        self.logger.configure_logger(name="RedisManager", level=LogLevel.INFO)
        self.exception_handler = ExceptionHandler()
        self.redis_client: redis.Redis | None = None

    async def connect(self) -> None:
        """Asynchronously connects to the Redis server."""
        try:
            self.redis_client = redis.Redis(
                host=self.host, port=self.port, db=self.db, decode_responses=True
            )
            # Check the connection
            await self.redis_client.ping()
            self.logger.log_info("Connected to Redis successfully.")
        except Exception as e:
            self.logger.log_error("Failed to connect to Redis.")
            raise RedisManagerError("Could not connect to Redis.") from e

    async def close(self) -> None:
        """Closes the Redis connection asynchronously."""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.log_info("Redis connection closed.")

    async def set_status(self, task_id: str, task_data: TaskData) -> None:
        """Stores the status of a task in Redis asynchronously."""
        try:
            if not self.redis_client:
                raise RedisManagerError("Redis client is not initialized.")
            await self.redis_client.set(task_id, json.dumps(task_data))
            self.logger.log_info(f"Task {task_id} status saved to Redis.")
        except Exception as e:
            self.logger.log_error(f"Failed to save task {task_id} to Redis: {e}")
            self.exception_handler.handle_exception(
                e, {"task_id": task_id, "task_data": task_data}
            )
            raise RedisManagerError(f"Error saving task {task_id} to Redis.") from e

    async def get_status(self, task_id: str) -> dict | None:
        """Retrieves the status of a task from Redis asynchronously."""
        try:
            if not self.redis_client:
                raise RedisManagerError("Redis client is not initialized.")
            task_data_str = await self.redis_client.get(task_id)
            if not task_data_str:
                self.logger.log_warning(f"Task {task_id} not found in Redis.")
                return None
            task_data = json.loads(task_data_str)
            self.logger.log_info(f"Task {task_id} retrieved from Redis: {task_data}")
            return task_data
        except Exception as e:
            self.logger.log_error(f"Failed to retrieve task {task_id} from Redis: {e}")
            self.exception_handler.handle_exception(e, {"task_id": task_id})
            raise RedisManagerError(
                f"Error retrieving task {task_id} from Redis."
            ) from e

    async def update_task_status(
        self, task_id: str, status: str, result: TaskData | None = None
    ) -> None:
        """Updates the status and result of a task in Redis asynchronously."""
        try:
            if not self.redis_client:
                raise RedisManagerError("Redis client is not initialized.")
            task_data_str = await self.redis_client.get(task_id)
            if not task_data_str:
                raise RedisManagerError(f"Task {task_id} not found in Redis.")
            task_data = json.loads(task_data_str)
            task_data["status"] = status
            task_data["result"] = result
            await self.redis_client.set(task_id, json.dumps(task_data))
            self.logger.log_info(
                f"Task {task_id} updated in Redis with status '{status}'."
            )
        except Exception as e:
            self.logger.log_error(f"Failed to update task {task_id} in Redis: {e}")
            self.exception_handler.handle_exception(
                e, {"task_id": task_id, "status": status, "result": result}
            )
            raise RedisManagerError(f"Error updating task {task_id} in Redis.") from e

    async def delete_task(self, task_id: str) -> None:
        """Deletes a task from Redis asynchronously."""
        try:
            if not self.redis_client:
                raise RedisManagerError("Redis client is not initialized.")
            result = await self.redis_client.delete(task_id)
            if result == 1:
                self.logger.log_info(f"Task {task_id} deleted from Redis.")
            else:
                self.logger.log_warning(
                    f"Task {task_id} not found in Redis during deletion."
                )
        except Exception as e:
            self.logger.log_error(f"Failed to delete task {task_id} from Redis: {e}")
            self.exception_handler.handle_exception(e, {"task_id": task_id})
            raise RedisManagerError(f"Error deleting task {task_id} from Redis.") from e
