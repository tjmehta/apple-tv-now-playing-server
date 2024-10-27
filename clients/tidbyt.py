# from tzlocal import get_localzone_name
import os
import asyncio

STAR_FILEPATH = os.path.join("appletv_tidbyt_app", "apple_tv.star")
WEBP_FILEPATH = os.path.join("appletv_tidbyt_app", "apple_tv.webp")
TIDBYT_APP_ID = "appletv"
PLAYING_API_HOST = "http://localhost"
PLAYING_API_PORT = 5005


async def run(cmd, timeout=30):  # 30 second timeout
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    print(f"[{cmd!r} started with pid {proc.pid}]")
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        print(f"[exited with {proc.returncode}]")
        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")
        return proc.returncode
    except asyncio.TimeoutError:
        print(f"Command timed out after {timeout} seconds")
        proc.terminate()
        return None


def singlequote(str):
    return "'" + str + "'"


async def render_and_push(tidbyt_config, max_retries=3, initial_delay=2):
    print("render_and_push: started")
    cmd = " ".join([
        "pixlet",
        "render",
        singlequote(STAR_FILEPATH),
        "apple_tv_mac_address=" + singlequote(tidbyt_config["appletv_mac"]),
        "apple_tv_now_playing_api_host=" + singlequote(PLAYING_API_HOST + ":" + str(PLAYING_API_PORT)),
        "treat_paused_as_idle=" + singlequote(tidbyt_config["treat_paused_as_idle"]),
        "&&",
        "pixlet",
        "push",
        singlequote(tidbyt_config["device_id"]),
        singlequote(WEBP_FILEPATH),
        "--api-token",
        singlequote(tidbyt_config["api_key"]),
        "--installation-id",
        singlequote(TIDBYT_APP_ID),
    ])

    for attempt in range(max_retries):
        try:
            print(f"render_and_push:Attempt {attempt + 1}: Executing command: {cmd}")
            result = await run(cmd)
            if result is not None:
                print(f"render_and_push: Command execution completed. Result: {result}")
                return result
            else:
                print(f"render_and_push: Attempt {attempt + 1}: Command execution timed out")
        except Exception as e:
            print(f"render_and_push: Attempt {attempt + 1}: render_and_push error: {str(e)}")

        if attempt < max_retries - 1:
            delay = initial_delay * (2 ** attempt)  # Exponential backoff
            print(f"render_and_push: Retrying in {delay} seconds...")
            await asyncio.sleep(delay)

    print(f"All {max_retries} attempts failed")
    return None
