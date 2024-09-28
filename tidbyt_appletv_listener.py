import asyncio
from pyatv import interface, const
import clients.tidbyt
import threading
import requests
import json

PAUSE_CHECK_INTERVAL = 15
MAX_PAUSE_COUNT = 4 # 15 * 4 = 1 minute

class TidbytAppletvListener(interface.PushListener):
    def __init__(self, tidbyt_config):
        self.tidbyt_config = tidbyt_config
        self.last_hash = None
        self.last_device_state = None
        self.pause_timer = None
        self.pause_count = 0

    def playstatus_update(self, updater, playstatus):
        if (
            playstatus.hash == self.last_hash
            and playstatus.device_state == self.last_device_state
        ):
            print("PlayStatus Update: Blocked:", self.last_device_state)
            return
        print("PlayStatus Update: New:", playstatus.title, playstatus.device_state)
        # hash changed, so render latest state, and cancel previous timeouts
        self.last_hash = playstatus.hash
        if self.pause_timer:
            self.pause_timer.cancel()
            self.pause_timer = None
            self.pause_count = 0

        self.schedule_render_and_push()
        # If device state is paused, set a timeout
        if playstatus.device_state == const.DeviceState.Paused:
            print("PlayStatus Update: Paused: Schedule Check", playstatus.title, playstatus.device_state)
            self.pause_timer = threading.Timer(PAUSE_CHECK_INTERVAL, self.check_still_paused, [playstatus])
            self.pause_timer.start()
            self.pause_count = 0

    def check_still_paused(self, playstatus):
        print("PlayStatus CheckStillPaused: Hash:", self.last_hash, playstatus.hash)
        if self.last_hash == playstatus.hash:
            print("PlayStatus CheckStillPaused: Fetch Status:", f"{clients.tidbyt.PLAYING_API_HOST}:{clients.tidbyt.PLAYING_API_PORT}/playing?mac={self.tidbyt_config['appletv_mac']}&width=22&height=22")
            # hit the playing api endpoint at PLAYING_API_HOST:PLAYING_API_PORT using tidbyt_config["appletv_mac"] as query param mac=
            # and if the response has device_state = idle then render and push to tidbyt
            url = f"{clients.tidbyt.PLAYING_API_HOST}:{clients.tidbyt.PLAYING_API_PORT}/playing?mac={self.tidbyt_config['appletv_mac']}&width=22&height=22"
            response = requests.get(url)
            payload = json.loads(response.text)

            print("PlayStatus CheckStillPaused: Fetch Result:", payload["title"], payload["device_state"])

            if payload["device_state"] == "DeviceState.Paused": # enum value didn't work
                if self.pause_count < MAX_PAUSE_COUNT:
                    print("PlayStatus CheckStillPaused: Still Paused, Schedule Check Again:", payload["title"], payload["device_state"], self.pause_count)
                    # still paused so schedule another check again after timeout
                    self.pause_timer = threading.Timer(PAUSE_CHECK_INTERVAL, self.check_still_paused, [playstatus])
                    self.pause_timer.start()
                    self.pause_count += 1
                else: # MAX_PAUSE_COUNT
                    print("PlayStatus CheckStillPaused: Max Pause Count Reached, Render Idle:", payload["title"], payload["device_state"])
                    self.schedule_render_and_push()
            if payload["device_state"] == "DeviceState.Idle": # enum value didn't work
                print("PlayStatus CheckStillPaused: Idle, Render Idle:", payload["title"], payload["device_state"])
                self.schedule_render_and_push()

    def schedule_render_and_push(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # If there's no running event loop, create a new one and run the task
            self.tidbyt_config["treat_paused_as_idle"] = "True" if self.pause_count >= MAX_PAUSE_COUNT else "False"
            asyncio.run(clients.tidbyt.render_and_push(self.tidbyt_config))
        else:
            # If there's a running event loop, schedule the task
            self.tidbyt_config["treat_paused_as_idle"] = "True" if self.pause_count >= MAX_PAUSE_COUNT else "False"
            loop.call_soon_threadsafe(lambda: asyncio.create_task(clients.tidbyt.render_and_push(self.tidbyt_config)))

    def playstatus_error(self, updater, exception):
        print("PlayStatus Error:", str(exception))

    def connection_lost(self, exception):
        print("Lost connection:", str(exception))
        raise Exception("apple tv disconnected: " + self.tidbyt_config["appletv_mac"])

    def connection_closed(self):
        print("Connection closed!")
