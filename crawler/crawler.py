import asyncio
from core.redis_manager import RedisManager
from core.rabbit_publisher import RabbitMQPublisher
from crawler.parser import TikTokLibraryParser
from json import loads


class Crawler:
    """
    Asynchronously consumes tasks from RabbitMQ, processes data, and publishes results.
    """

    def __init__(self, rabbit_config_path: str, redis_config_path: str):
        self.rabbit_publisher = RabbitMQPublisher(rabbit_config_path)
        self.redis_manager = RedisManager(redis_config_path)
        self.parser = TikTokLibraryParser()
        self.task_queue = "crawler.task"
        self.result_queue = "crawler.result"

    async def connect(self):
        """
        Establishes connections to RabbitMQ and Redis.
        """
        await self.rabbit_publisher.connect()
        await self.redis_manager.connect()

    async def process_task(self, message: dict):
        """
        Processes a single task message asynchronously.
        """
        try:
            task_id = message.get("task_id")
            keyword = message.get("keyword")

            if not task_id or not keyword:
                raise ValueError(
                    "Invalid message format: 'task_id' or 'keyword' missing."
                )

            result = await asyncio.to_thread(
                self.parser.search_ads, region="all", adv_name=keyword
            )
            result_message = {
                "task_id": task_id,
                "status": "completed",
                "result": result,
            }

            await self.rabbit_publisher.publish(
                queue=self.result_queue, message=result_message
            )
            await self.redis_manager.update_task_status(task_id, "completed", result)  # type: ignore

        except Exception as e:
            error_message = {
                "task_id": message.get("task_id", "unknown"),
                "status": "failed",
                "error": str(e),
            }
            await self.rabbit_publisher.publish(
                queue=self.result_queue, message=error_message
            )

    async def consume_tasks(self):
        """
        Asynchronously consumes tasks from the RabbitMQ queue.
        """
        queue = await self.rabbit_publisher.channel.declare_queue(
            self.task_queue, durable=True
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        task_data = loads(message.body)
                        await self.process_task(task_data)
                    except Exception as e:
                        print(f"Error processing message: {e}")

    async def close(self):
        """
        Closes connections to RabbitMQ and Redis.
        """
        await self.rabbit_publisher.close_connection()
        await self.redis_manager.close()
