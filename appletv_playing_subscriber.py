import asyncio
from pyatv import interface


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
        self.atv.power.listener = listener

    def start(self):
        self.atv.push_updater.start()

    def stop(self):
        self.atv.push_updater.stop()
