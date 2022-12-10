from tzlocal import get_localzone_name
import os
import asyncio

STAR_FILEPATH = os.path.join("appletv_tidbyt_app", "apple_tv.star")
WEBP_FILEPATH = os.path.join("appletv_tidbyt_app", "apple_tv.webp")
TIDBYT_APP_ID = "appletv"


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    print(f"[{cmd!r} exited with {proc.returncode}]")
    # if stdout:
    #     print(f"[stdout]\n{stdout.decode()}")
    # if stderr:
    #     print(f"[stderr]\n{stderr.decode()}")


def singlequote(str):
    return "'" + str + "'"


def render_and_push(tidbyt_config):
    print("render_and_push")
    try:
        cmd = " ".join(
            [
                "pixlet",
                "render",
                singlequote(STAR_FILEPATH),
                "timezone=" + singlequote(get_localzone_name()),
                "apple_tv_mac_address=" + singlequote(tidbyt_config["appletv_mac"]),
                "apple_tv_now_playing_api_host=" + singlequote("http://localhost:5005"),
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
        asyncio.create_task(run(cmd))

    except Exception as e:
        print("render_and_push error:", str(e))
