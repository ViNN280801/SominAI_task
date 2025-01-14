from core.redis_manager import RedisManager
from core.rabbit_publisher import RabbitMQPublisher
from modules.alert_handler import AlertHandler, AlertDestination
from json import loads


class ResultProcessor:
    """
    Asynchronously processes completed tasks from the `crawler.result` queue.
    """

    def __init__(
        self, rabbit_config_path: str, redis_config_path: str, alert_config: dict
    ):
        self.redis_manager = RedisManager(redis_config_path)
        self.rabbit_publisher = RabbitMQPublisher(rabbit_config_path)
        self.alert_handler = AlertHandler.get_instance(alert_config)
        self.result_queue = "crawler.result"

    async def connect(self):
        """
        Establishes connections to RabbitMQ and Redis.
        """
        await self.rabbit_publisher.connect()
        await self.redis_manager.connect()

    async def process_results(self):
        """
        Processes results from the RabbitMQ result queue asynchronously.
        """
        queue = await self.rabbit_publisher.channel.declare_queue(
            self.result_queue, durable=True
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        result_data = loads(message.body)
                        task_id = result_data.get("task_id")
                        status = result_data.get("status")
                        result = result_data.get("result")

                        if not task_id or not status:
                            raise ValueError(
                                "Invalid task data: Missing 'task_id' or 'status'."
                            )

                        await self.redis_manager.update_task_status(
                            task_id, status, result
                        )

                        # Send alerts based on task status
                        message_text = (
                            f"Task {task_id} completed successfully."
                            if status == "completed"
                            else f"Task {task_id} failed."
                        )
                        await self.alert_handler.send_alert(
                            AlertDestination.TELEGRAM, message_text
                        )
                        await self.alert_handler.send_alert(
                            AlertDestination.LOGGING, message_text
                        )

                    except Exception as e:
                        print(f"Error processing result: {e}")

    async def close(self):
        """
        Closes connections to RabbitMQ and Redis.
        """
        await self.rabbit_publisher.close_connection()
        await self.redis_manager.close()
