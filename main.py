import argparse
import asyncio
import uvicorn

from app.main import start_scheduler, app


def run_scheduler():
    # 为 APScheduler 创建并设置独立事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_scheduler(loop)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass


def run_api():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MessageBackend entrypoint")
    parser.add_argument("--scheduler", action="store_true", help="启动独立定时任务调度器")
    args = parser.parse_args()

    if args.scheduler:
        run_scheduler()
    else:
        run_api()