from os import path, remove, listdir
import pathlib

ATV_PAIRING_DIRPATH = path.join(".appletv", ".appletv_pairings")


def create_dir():
    filepath = ATV_PAIRING_DIRPATH
    pathlib.Path(filepath).mkdir(parents=True, exist_ok=True)


def get_filepath(mac=None):
    create_dir()
    if mac:
        return path.join(ATV_PAIRING_DIRPATH, mac)
    else:
        return ATV_PAIRING_DIRPATH


def list_macs():
    filepath = get_filepath()

    return listdir(filepath)


def has(mac):
    filepath = get_filepath(mac)
    return path.isfile(filepath)


def save(mac, credentials):
    filepath = get_filepath(mac)
    with open(filepath, "w") as f:
        f.write(credentials)


def get(mac):
    filepath = get_filepath(mac)
    with open(filepath, "r") as f:
        return f.read(300)


def remove(mac):
    filepath = get_filepath(mac)
    if path.isfile(filepath):
        remove(filepath)
