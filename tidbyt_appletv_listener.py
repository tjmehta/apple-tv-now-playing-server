from pyatv import interface
import clients.tidbyt


class TidbytAppletvListener(interface.PushListener):
    def __init__(self, tidbyt_config):
        self.tidbyt_config = tidbyt_config
        self.last_hash = None
        self.last_device_state = None

    def playstatus_update(self, updater, playstatus):
        if (
            playstatus.hash == self.last_hash
            and playstatus.device_state == self.last_device_state
        ):
            print("PlayStatus Update: Blocked:", self.last_device_state)
            return
        print("PlayStatus Update: New:", playstatus.title, playstatus.device_state)
        self.last_hash = playstatus.hash
        clients.tidbyt.render_and_push(self.tidbyt_config)

    def playstatus_error(self, updater, exception):
        print("PlayStatus Error:", str(exception))

    def connection_lost(self, exception):
        print("Lost connection:", str(exception))
        raise Exception("apple tv disconnected: " + self.tidbyt_config["appletv_mac"])

    def connection_closed(self):
        print("Connection closed!")
