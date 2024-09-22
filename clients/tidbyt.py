# from tzlocal import get_localzone_name
import os
import asyncio

STAR_FILEPATH = os.path.join("appletv_tidbyt_app", "apple_tv.star")
WEBP_FILEPATH = os.path.join("appletv_tidbyt_app", "apple_tv.webp")
TIDBYT_APP_ID = "appletv"
PLAYING_API_HOST = "http://localhost"
PLAYING_API_PORT = 5005


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    print(f"[{cmd!r} exited with {proc.returncode}]")
    # if stdout:
    #     print(f"[stdout]\n{stdout.decode()}")
    if stderr:
        print(f"[stderr]\n{stderr.decode()}")


def singlequote(str):
    return "'" + str + "'"


async def render_and_push(tidbyt_config):
    print("render_and_push")
    try:
        cmd = " ".join(
            [
                "pixlet",
                "render",
                singlequote(STAR_FILEPATH),
                # "timezone=" + singlequote(get_localzone_name()),
                "apple_tv_mac_address=" + singlequote(tidbyt_config["appletv_mac"]),
                "apple_tv_now_playing_api_host=" + singlequote(PLAYING_API_HOST + ":" + str(PLAYING_API_PORT)),
                "treat_paused_as_idle=" + singlequote(tidbyt_config["treat_paused_as_idle"]),
                ####
                "&&",
                ####
                "pixlet",
                "push",
                singlequote(tidbyt_config["device_id"]),
                singlequote(WEBP_FILEPATH),
                "--api-token",
                singlequote(tidbyt_config["api_key"]),
                "--installation-id",
                singlequote(TIDBYT_APP_ID),
            ]
        )
        return await run(cmd)  # Return the coroutine
    except Exception as e:
        print("render_and_push error:", str(e))
        return None  # Return None in case of an error
