import uuid
from quart import Blueprint, request, jsonify
from core.rabbit_publisher import RabbitMQPublisher
from core.redis_manager import RedisManager
from configs.config_loader import ConfigLoader
from modules.exception_handler import ExceptionHandler

routes = Blueprint("routes", __name__)

RABBIT_PUBLISHER = RabbitMQPublisher("configs/rabbitmq.yaml")
REDIS_MANAGER = RedisManager("configs/config.yaml")
CONFIG = ConfigLoader.load_config("configs/config.yaml")
DEFAULT_REGION = CONFIG.get(
    "default_region", "BE"
)  # Default to "BE" (Belgium) if not configured


@routes.before_app_serving
async def init_connections():
    """
    Runs once before the Quart app starts serving requests.
    Ensures RabbitMQ and Redis connections are initialized.
    """
    await RABBIT_PUBLISHER.connect()
    await REDIS_MANAGER.connect()


@routes.route("/crawl", methods=["POST"])
async def crawl():
    """
    Endpoint to add a crawling task to the RabbitMQ queue.
    """
    data = await request.get_json()
    if not data or "keyword" not in data:
        return jsonify({"error": "Missing 'keyword' in request body"}), 400

    region = data.get("region", DEFAULT_REGION)
    task_id = str(uuid.uuid4())

    try:
        await RABBIT_PUBLISHER.publish(
            queue="crawler.task",
            message={"task_id": task_id, "keyword": data["keyword"], "region": region},
        )
        await REDIS_MANAGER.set_status(
            task_id,
            {
                "status": "queued",
                "keyword": data["keyword"],
                "region": region,
                "result": None,
            },
        )
        return jsonify({"task_id": task_id})
    except Exception as e:
        return jsonify({"error": f"Failed to enqueue task: {e}"}), 500


@routes.route("/result/<task_id>", methods=["GET"])
async def get_result(task_id):
    try:
        task_status = await REDIS_MANAGER.get_status(task_id)
        if task_status is None:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task_status)
    except Exception as e:
        context = {
            "path": request.path,
            "method": request.method,
        }
        ExceptionHandler.handle_exception(e, context)
        return jsonify({"error": f"Failed to fetch task status: {e}"}), 500
