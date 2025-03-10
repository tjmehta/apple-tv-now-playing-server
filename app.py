import asyncio
import base64
import re
import sys
import signal

from pyatv import scan, pair, connect
from pyatv.const import Protocol
from quart import Quart, render_template, request, redirect, url_for


import storage.appletv_pairings
import storage.tidbyt_configs
from utils.validate_int import validate_int
from utils.validate_string import validate_string
from utils.jsonify_playing import jsonify_playing
from appletv_playing_subscriber import AppletvPlayingSubscriber
from tidbyt_appletv_listener import TidbytAppletvListener
from clients.tidbyt import PLAYING_API_PORT

# Make sure unhandled exceptions in tasks crash the service
def handle_exception(loop, context):
    exception = context.get('exception')
    if exception:
        print(f"Unhandled exception: {exception}", file=sys.stderr)
        print("Crashing service to trigger restart", file=sys.stderr)
        sys.exit(1)  # Exit with error code to ensure Docker restarts the service

app = Quart(__name__)


### PAIRING ROUTES

# memory storage..
pairings = {}
atv_subcribers = {}


@app.route("/")
async def index_route():
    paired_atv_macs = storage.appletv_pairings.list_macs()
    # render
    return await render_template("index.html", paired_atv_macs=paired_atv_macs)


@app.route("/scan")
async def scan_route():
    loop = asyncio.get_event_loop()

    # parse query params
    name = validate_string(request.args.get("name"))
    ip = validate_string(request.args.get("ip"))
    mac = validate_string(request.args.get("mac"))
    print([mac])

    # scan airplay devices
    hosts = [ip] if ip != None else None
    identifier = mac
    atvs = await scan(
        loop=loop, hosts=hosts, identifier=identifier, protocol=Protocol.AirPlay
    )

    # filter airplay devices using query params
    filtered_atvs = list(
        filter(
            lambda atv: (name == None and ip == None and identifier == None)
            or name == atv.name
            or ip == str(atv.address)
            or identifier == str(atv.identifier),
            atvs,
        )
    )

    # render
    return await render_template("scan.html", atvs=filtered_atvs)


@app.route("/pair")
async def pair_route():
    loop = asyncio.get_event_loop()

    # parse query params
    mac = validate_string(request.args.get("mac"))
    if mac == None:
        return redirect(url_for("scan_route"))

    atv_pair_exists = storage.appletv_pairings.has(mac)
    if atv_pair_exists:
        # redirect but make sure mac is in query params
        return redirect(url_for("pair_exists_route", mac=mac))

    # check if pairing in progress
    if mac in pairings and pairings[mac]:
        return await render_template("pair.html", mac=mac)

    pairings[mac] = "waiting"

    identifier = mac
    atvs = await scan(loop=loop, identifier=identifier, protocol=Protocol.AirPlay)

    if len(atvs) == 0:
        raise Exception("apple tv not found: " + identifier)

    # scan airplay devices
    loop = asyncio.get_event_loop()
    pairings[mac] = await pair(loop=loop, config=atvs[0], protocol=Protocol.AirPlay)
    await pairings[mac].begin()

    return await render_template("pair.html", mac=mac)


@app.route("/pair_pin")
async def pair_pin_route():
    # parse query params
    mac = validate_string(request.args.get("mac"))
    if mac == None:
        return redirect(url_for("scan_route"))
    pin = validate_string(request.args.get("pin"))
    if pin == None:
        return redirect(url_for("pair_route"))

    atv_pair_exists = storage.appletv_pairings.has(mac)
    if atv_pair_exists:
        return redirect(url_for("pair_exists_route", mac=mac))

    # check if pairing in progress
    if not mac in pairings:
        return redirect(url_for("pair_route"))

    if pairings[mac] == "waiting":
        return "Waiting on pairing, try again in a few seconds.."
    pairing = pairings[mac]

    if not pairing.device_provides_pin:
        await pairing.close()
        del pairings[mac]
        return "unexpected: server provides pin??? refresh and try another device."

    pairing.pin(pin)
    await pairing.finish()

    if pairing.has_paired:
        storage.appletv_pairings.save(mac, pairing.service.credentials)
        await pairing.close()
        del pairings[mac]
        return await render_template("pair_exists.html", mac=mac)
    else:
        await pairing.close()
        del pairings[mac]
        return "failed.. refresh and try again"

@app.route("/pair_exists")
async def pair_exists_route():
    # parse query params
    mac = validate_string(request.args.get("mac"))

    if mac == None:
        return redirect(url_for("index_route"))

    atv_pair_exists = storage.appletv_pairings.has(mac)

    if not atv_pair_exists:
        return redirect(url_for("index_route"))

    # find tidbyt pairig
    tidbyt_device_ids = storage.tidbyt_configs.list_device_ids()
    # loop through each id and get each tidbyt config
    for tidbyt_device_id in tidbyt_device_ids:
        tidbyt_config = storage.tidbyt_configs.get(tidbyt_device_id)
        if "appletv_mac" in tidbyt_config and tidbyt_config["appletv_mac"] == mac:
            return await render_template("pair_exists.html", mac=mac, tidbyt_device_id=tidbyt_device_id)

    return await render_template("pair_exists.html", mac=mac)


@app.route("/delete_pair")
async def delete_pair_route():
    # parse query params
    mac = validate_string(request.args.get("mac"))
    if mac == None:
        raise Exception("mac (query param) is required")

    # check if pairing in progress
    if mac in pairings and pairings[mac] == "waiting":
        return "Waiting on pairing, try again in a few seconds.."

    storage.appletv_pairings.remove(mac)

    if mac in pairings and pairings[mac]:
        pairing = pairings[mac]
        await pairing.close()
        del pairings[mac]

    return redirect(url_for("pair_route"))


### NOW PLAYING ROUTES


@app.route("/playing")
async def playing_route():
    loop = asyncio.get_event_loop()

    # parse query params
    mac = validate_string(request.args.get("mac"))
    width = validate_int(request.args.get("width"))
    height = validate_int(request.args.get("height"))

    result = {}
    if mac == None:
        return {"message": "'mac' query parameter is required"}, 400

    atv_pair_exists = storage.appletv_pairings.has(mac)
    if not atv_pair_exists:
        return {"message": "device with mac is not paired"}, 409

    airplay_creds = storage.appletv_pairings.get(mac)

    if airplay_creds == "":
        return {"message": "device with mac is not paired"}, 409

    identifier = mac
    atvs = await scan(loop=loop, identifier=identifier, protocol=Protocol.AirPlay)

    if len(atvs) == 0:
        return {"message": "device with mac not found"}, 404

    # get config
    config = atvs[0]
    config.set_credentials(Protocol.AirPlay, airplay_creds)

    # connect and get playing
    atv = await connect(loop=loop, config=config)
    playing = await atv.metadata.playing()
    json = jsonify_playing(playing)
    artwork = await atv.metadata.artwork(height=height, width=width)
    if artwork and len(artwork.bytes):
        json.update(
            {
                "artwork": {
                    "id": atv.metadata.artwork_id,
                    "bytes": re.sub(
                        "^b'([^']+)'$", r"\1", str(base64.b64encode(artwork.bytes))
                    ),
                    "mimetype": artwork.mimetype,
                    "height": artwork.height,
                    "width": artwork.width,
                }
            }
        )
    print("/playing:", json["title"], json["device_state"])
    atv.close()
    return json, 200, {"Content-Type": "application/json"}


### TIDBYT ROUTES


@app.route("/tidbyt")
async def tidbyt_route():
    loop = asyncio.get_event_loop()

    # parse query params
    macs = storage.appletv_pairings.list_macs()

    # scan airplay devices
    identifier = validate_string(request.args.get("mac"))
    atvs = await scan(
        loop=loop, hosts=None, identifier=identifier, protocol=Protocol.AirPlay
    )

    # filter airplay devices using query params
    filtered_atvs = list(
        filter(
            lambda atv: str(atv.identifier) in macs,
            atvs,
        )
    )

    # render
    return await render_template("tidbyt.html", atvs=filtered_atvs)


@app.route("/tidbyt_exists")
async def tidbyt_exists_route():
    tidbyt_device_id = validate_string(request.args.get("tidbyt_device_id"))
    if tidbyt_device_id is None:
        return "tidbyt_device_id (query param) is required", 400

    if not storage.tidbyt_configs.has(tidbyt_device_id):
        return f"No configuration found for device ID: {tidbyt_device_id}", 404

    existing_tidbyt_config = storage.tidbyt_configs.get(tidbyt_device_id)
    return await render_template(
        "tidbyt_config_exists.html",
        tidbyt_device_id=tidbyt_device_id,
        tidbyt_config=existing_tidbyt_config
    )

@app.route("/tidbyt_save")
async def tidbyt_save_route():
    loop = asyncio.get_event_loop()

    # parse query params
    atv_mac = validate_string(request.args.get("mac"))
    tidbyt_device_id = validate_string(request.args.get("tidbyt_device_id"))
    tidbyt_api_key = validate_string(request.args.get("tidbyt_api_key"))

    if any(param is None for param in [atv_mac, tidbyt_device_id, tidbyt_api_key]):
        return redirect(url_for("tidbyt_route"))

    # check if atv pairing exists
    if not storage.appletv_pairings.has(atv_mac):
        return redirect(url_for("tidbyt_route"))

    tidbyt_config = {
        "device_id": tidbyt_device_id,
        "api_key": tidbyt_api_key,
        "appletv_mac": atv_mac,
        "treat_paused_as_idle": 'False', # used to check if the apple tv is paused a long time
    }

    # check if tidbyt already saved
    if storage.tidbyt_configs.has(tidbyt_device_id):
        existing_tidbyt_config = storage.tidbyt_configs.get(tidbyt_device_id)

        # Check if all values match
        if all(tidbyt_config.get(key) == existing_tidbyt_config.get(key) for key in tidbyt_config):
            return redirect(url_for("tidbyt_exists_route", tidbyt_device_id=tidbyt_device_id))

        # unsubscribe from old config, assumed it's not paired with different tidbyt device
        await delete_tidbyt_config(tidbyt_device_id)

    # listen
    await tidbyt_appletv_subscribe(loop, tidbyt_config)

    # save config
    storage.tidbyt_configs.save(tidbyt_device_id, tidbyt_config)
    return redirect(url_for("tidbyt_exists_route", tidbyt_device_id=tidbyt_device_id))


async def tidbyt_appletv_subscribe(loop, tidbyt_config):
    atv_mac = tidbyt_config["appletv_mac"]
    print("subscribe", atv_mac)
    identifier = atv_mac
    atvs = await scan(loop=loop, identifier=identifier, protocol=Protocol.AirPlay)

    if len(atvs) == 0:
        raise Exception("apple tv not found: " + identifier)

    airplay_creds = storage.appletv_pairings.get(atv_mac)
    if airplay_creds == "":
        raise Exception("apple tv with mac is not paired: " + identifier)

    atv_config = atvs[0]

    if atv_config.identifier in atv_subcribers:
        print("subscribe: already subscribed", atv_mac)

    async def listen():
        atv_config.set_credentials(Protocol.AirPlay, airplay_creds)
        atv = await connect(loop=loop, config=atv_config)
        listener = TidbytAppletvListener(tidbyt_config)
        sub = AppletvPlayingSubscriber(atv, listener, listener)
        sub.start()
        atv_subcribers[atv_config.identifier] = sub
        try:
            # go ahead and update the tidbyt device
            listener.schedule_render_and_push()
        except Exception as e:
            print("listen error:", str(e))

    app.add_background_task(listen)


@app.route("/delete_tidbyt_config")
async def delete_tidbyt_config_route():
    # parse query params
    tidbyt_device_id = validate_string(request.args.get("tidbyt_device_id"))
    if tidbyt_device_id == None:
        raise Exception("tidbyt_device_id (query param) is required")

    try:
        atv_mac = await delete_tidbyt_config(tidbyt_device_id)
        return redirect(url_for("pair_exists_route", mac=atv_mac))
    except ValueError as e:
        # Handle the error, perhaps by rendering an error template or redirecting to an error page
        return str(e), 400  # Bad Request

async def delete_tidbyt_config(tidbyt_device_id):
    tidbyt_config = storage.tidbyt_configs.get(tidbyt_device_id)
    if not tidbyt_config:
        raise ValueError(f"No configuration found for device ID: {tidbyt_device_id}")

    atv_mac = tidbyt_config.get("appletv_mac")
    if not atv_mac:
        raise ValueError(f"No Apple TV MAC address found for device ID: {tidbyt_device_id}")

    if atv_mac in atv_subcribers:
        atv_subcribers[atv_mac].stop()
        del atv_subcribers[atv_mac]

    storage.tidbyt_configs.remove(tidbyt_device_id)
    return atv_mac


async def init_subscriptions():
    print("init subscriptions")
    loop = asyncio.get_event_loop()
    tidbyt_device_ids = storage.tidbyt_configs.list_device_ids()
    for device_id in tidbyt_device_ids:
        tidbyt_config = storage.tidbyt_configs.get(device_id)
        print(f"Initializing subscription for device: {device_id}", len(tidbyt_config))
        try:
            await tidbyt_appletv_subscribe(loop, tidbyt_config)
            print(f"Successfully subscribed to device: {device_id}")
        except Exception as e:
            print(f"Failed to subscribe to device {device_id}. Error: {str(e)}")


async def unsubscribe_all():
    for atv_mac in atv_subcribers:
        atv_subcribers[atv_mac].stop()


@app.before_serving
async def after_listen():
    # Set the exception handler for the event loop
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(handle_exception)
    await init_subscriptions()


@app.after_serving
async def shutdown():
    await unsubscribe_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PLAYING_API_PORT)
