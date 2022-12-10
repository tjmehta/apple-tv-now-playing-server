from os import path, remove, listdir, makedirs
import pathlib
import json

TIDBYT_CONFIG_DIRPATH = path.join(".appletv", ".tidbyt_config")


def create_dir():
    filepath = TIDBYT_CONFIG_DIRPATH
    pathlib.Path(filepath).mkdir(parents=True, exist_ok=True)


def get_filepath(tidbyt_device_id=None):
    create_dir()
    if tidbyt_device_id:
        return path.join(TIDBYT_CONFIG_DIRPATH, tidbyt_device_id)
    else:
        return TIDBYT_CONFIG_DIRPATH


def list_device_ids():
    filepath = get_filepath()

    return listdir(filepath)


def has(tidbyt_device_id):
    filepath = get_filepath(tidbyt_device_id)
    return path.isfile(filepath)


def remove(tidbyt_device_id):
    filepath = get_filepath(tidbyt_device_id)
    if path.isfile(filepath):
        remove(filepath)


def save(tidbyt_device_id, config):
    with open(get_filepath(tidbyt_device_id), "w") as f:
        f.write(json.dumps(config))


def get(tidbyt_device_id):
    filepath = get_filepath(tidbyt_device_id)
    with open(filepath, "r") as f:
        contents = f.read(1000)
        try:
            config = json.loads(contents)
            return config
        except Exception as e:
            print(str(e))
            remove(tidbyt_device_id)
            return None
