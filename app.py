import asyncio
from os import path, remove
from functools import reduce
import base64
import re

from pyatv import scan, pair, connect
from pyatv.const import Protocol
from quart import Quart, render_template, request, redirect, url_for, jsonify

app = Quart(__name__)


### PAIRING ROUTES

# HACK: memory stack.. to keep pairings around
pairings = {}


@app.route("/")
async def index_route():
    # render
    return await render_template("index.html")


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
    filtered_atvs = filter(
        lambda atv: (name == None and ip == None and identifier == None)
        or name == atv.name
        or ip == str(atv.address)
        or identifier == str(atv.identifier),
        atvs,
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

    filepath = path.join(".appletv_pairings", mac)
    if path.isfile(filepath):
        return await render_template("pair_exists.html", mac=mac)

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

    filepath = path.join(".appletv_pairings", mac)
    if path.isfile(filepath):
        return redirect(url_for("pair_route"))

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
        write_file(mac, pairing.service.credentials)
        await pairing.close()
        del pairings[mac]
        return await render_template("pair_exists.html", mac=mac)
    else:
        await pairing.close()
        del pairings[mac]
        return "failed.. refresh and try again"


@app.route("/delete_pair")
async def delete_pair_route():
    # parse query params
    mac = validate_string(request.args.get("mac"))
    if mac == None:
        raise Exception("mac (query param) is required")

    # check if pairing in progress
    if mac in pairings and pairings[mac] == "waiting":
        return "Waiting on pairing, try again in a few seconds.."

    filepath = path.join(".appletv_pairings", mac)
    if path.isfile(filepath):
        remove(filepath)

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

    filepath = path.join(".appletv_pairings", mac)
    if not path.isfile(filepath):
        return {"message": "device with mac is not paired"}, 409

    with open(filepath, "r") as f:
        airplay_creds = f.read(300)

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
    print(json)

    return json, 200, {"Content-Type": "application/json"}


### UTILS
def write_file(filename, content):
    with open(path.join(".appletv_pairings", filename), "w") as f:
        f.write(content)


def validate_string(string):
    if string == None:
        return None
    if len(string):
        return string
    return None


def validate_int(string):
    if string == None:
        return None
    if len(string):
        return int(string)
    return None


def jsonify_playing(playing):
    def reducer(memo, prop):
        val = getattr(playing, prop) or ""
        memo[prop] = str(val)
        return memo

    return reduce(reducer, playing._PROPERTIES, {})


app.run(host="0.0.0.0", port=5005)
