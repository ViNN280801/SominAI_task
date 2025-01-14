import sys
import signal
import multiprocessing
from api.app import create_app
from crawler.crawler import Crawler
from configs.config_loader import ConfigLoader


def run_quart():
    config = ConfigLoader.load_config("configs/config.yaml")
    app_settings = config.get("app", {})
    host = app_settings.get("host", "0.0.0.0")
    port = app_settings.get("port", 8000)

    app = create_app()
    app.run(host=host, port=port, debug=False)


def run_crawler():
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    crawler = Crawler("configs/rabbitmq.yaml", "configs/config.yaml")

    async def consume():
        await crawler.connect()
        await crawler.consume_tasks()

    try:
        loop.run_until_complete(consume())
    finally:
        loop.close()


def main():
    quart_proc = multiprocessing.Process(target=run_quart)
    crawler_proc = multiprocessing.Process(target=run_crawler)

    quart_proc.start()
    crawler_proc.start()

    def handle_sigint(sig, frame):
        print("\nReceived Ctrl+C (SIGINT). Stopping processes...")
        quart_proc.terminate()
        crawler_proc.terminate()
        quart_proc.join()
        crawler_proc.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    # Wait for the processes (blocking)
    quart_proc.join()
    crawler_proc.join()


if __name__ == "__main__":
    main()
