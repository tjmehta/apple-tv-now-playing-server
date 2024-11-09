import asyncio
import logging
from pyatv import interface
from pyatv.exceptions import BlockedStateError


class AppletvPlayingSubscriber:
    def __init__(
        self,
        atv: interface.AppleTV,
        push_listener: interface.PushListener,
        listener: interface.DeviceListener,
    ):
        self.listener = listener  # keep it around, atv uses weak references
        self.atv = atv
        self.atv.push_updater.listener = push_listener
        self.atv.device_info.listener = listener
        self.ping_interval = 60 * 30  # 30 min in seconds
        self.ping_task = None

    async def start_ping(self):
        while True:
            await self.ping_with_retry()
            print("ping success")
            await asyncio.sleep(self.ping_interval)

    async def ping_with_retry(self, max_retries=3, initial_delay=1):
        for attempt in range(max_retries):
            try:
                await self.ping_atv()
                return
            except Exception as e:
                delay = initial_delay * (2 ** attempt)
                logging.warning(f"Ping failed, retry {attempt + 1}/{max_retries} in {delay}s: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    raise e

    async def ping_atv(self):
        await self.atv.metadata.playing()

    def handle_ping_task_exception(self, task):
        if task.cancelled():
            logging.info("Ping task was cancelled")
        elif task.exception() is not None:
            # Let the exception propagate and crash the process
            # Docker will handle the restart
            logging.info("Ping task exception")
            raise task.exception()

    def start(self):
        self.atv.push_updater.start()
        self.ping_task = asyncio.ensure_future(self.start_ping())
        self.ping_task.add_done_callback(self.handle_ping_task_exception)

    def stop(self):
        self.atv.push_updater.stop()
        self.ping_task.cancel()
