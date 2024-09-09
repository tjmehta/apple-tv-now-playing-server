from pyatv import interface, const
import clients.tidbyt
import threading
import requests
import json


class TidbytAppletvListener(interface.PushListener):
    def __init__(self, tidbyt_config):
        self.tidbyt_config = tidbyt_config
        self.last_hash = None
        self.last_device_state = None
        self.pause_timer = None

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
        clients.tidbyt.render_and_push(self.tidbyt_config)
        # If device state is paused, set a timeout
        if playstatus.device_state == const.DeviceState.Paused:
            print("PlayStatus Update: Paused: Schedule Check", playstatus.title, playstatus.device_state)
            self.pause_timer = threading.Timer(30, self.handle_still_paused, [playstatus])
            self.pause_timer.start()

    def handle_still_paused(self, playstatus):
        print("PlayStatus Check: Check Hash:", self.last_hash, playstatus.hash)
        if self.last_hash == playstatus.hash:
            print("PlayStatus Check: Fetch Status:", f"{clients.tidbyt.PLAYING_API_HOST}:{clients.tidbyt.PLAYING_API_PORT}/playing?mac={self.tidbyt_config['appletv_mac']}")
            # hit the playing api endpoint at PLAYING_API_HOST:PLAYING_API_PORT using tidbyt_config["appletv_mac"] as query param mac=
            # and if the response has device_state = idle then render and push to tidbyt
            url = f"{clients.tidbyt.PLAYING_API_HOST}:{clients.tidbyt.PLAYING_API_PORT}/playing?mac={self.tidbyt_config['appletv_mac']}"
            response = requests.get(url)
            data = json.loads(response.text)

            data_device_state = data.get("device_state")
            data_title = data.get("title")
            print("PlayStatus Update: Fetched:", data_title, data_device_state)

            if data_device_state == const.DeviceState.Paused:
                print("PlayStatus Check: Unchanged: Schedule Check", data_title, data_device_state)
                # still paused so schedule another check in 10 seconds
                self.pause_timer = threading.Timer(30, self.handle_still_paused, [playstatus])
                self.pause_timer.start()
            if data_device_state == const.DeviceState.Idle:
                print("PlayStatus Check: New:", data_title, data_device_state)
                # not paused so render and push to tidbyt
                clients.tidbyt.render_and_push(self.tidbyt_config)


    def playstatus_error(self, updater, exception):
        print("PlayStatus Error:", str(exception))

    def connection_lost(self, exception):
        print("Lost connection:", str(exception))
        raise Exception("apple tv disconnected: " + self.tidbyt_config["appletv_mac"])

    def connection_closed(self):
        print("Connection closed!")
