import json

from sata_library.errors import LibraryError
from sata_library.model import Disk

LSBLK_COLUMNS = "NAME,SERIAL,WWN,SIZE,TYPE,TRAN,PATH"


def disks_from_lsblk(payload: str) -> list[Disk]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise LibraryError("bad_lsblk", "lsblk вернул не JSON") from exc
    devices = data.get("blockdevices")
    if not isinstance(devices, list):
        raise LibraryError("bad_lsblk", "в JSON нет списка blockdevices")
    return [_disk(item) for item in devices if item.get("type") == "disk"]


def _disk(item: dict) -> Disk:
    return Disk(
        name=_text(item.get("name")),
        serial=_text(item.get("serial")),
        wwn=_text(item.get("wwn")),
        size=_text(item.get("size")),
        tran=_text(item.get("tran")),
        path=_text(item.get("path")),
    )


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
