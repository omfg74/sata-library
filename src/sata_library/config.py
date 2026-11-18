import tomllib
from pathlib import Path

from sata_library.errors import LibraryError
from sata_library.model import DiskEntry, LibraryConfig


def load_config(path: str | Path) -> LibraryConfig:
    try:
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise LibraryError("config", f"не читается {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise LibraryError("config", "файл манифеста не TOML") from exc

    pause = data.get("spin_pause_s")
    if isinstance(pause, bool) or not isinstance(pause, (int, float)) or pause <= 0:
        raise LibraryError("config", "spin_pause_s — число секунд больше нуля")

    raw_disks = data.get("disk")
    if not isinstance(raw_disks, list) or not raw_disks:
        raise LibraryError("config", "нужен хотя бы один [[disk]]")

    disks: list[DiskEntry] = []
    seen: set[tuple[int, int]] = set()
    for item in raw_disks:
        entry = _entry(item)
        key = (entry.slot, entry.index)
        if key in seen:
            raise LibraryError("config", f"слот {entry.slot} диск {entry.index} указан дважды")
        seen.add(key)
        disks.append(entry)
    return LibraryConfig(spin_pause_s=float(pause), disks=tuple(disks))


def _entry(item: object) -> DiskEntry:
    if not isinstance(item, dict):
        raise LibraryError("config", "запись disk должна быть таблицей")
    slot = _place(item.get("slot"), "слот")
    index = _place(item.get("index"), "диск")
    serial = item.get("serial", "")
    path_contains = item.get("path_contains", "")
    mount = item.get("mount", "")
    if not isinstance(serial, str):
        raise LibraryError("config", f"серийник слота {slot} диска {index} должен быть строкой")
    if not isinstance(path_contains, str):
        raise LibraryError("config", f"path_contains слота {slot} диска {index} должен быть строкой")
    if not isinstance(mount, str):
        raise LibraryError("config", f"mount слота {slot} диска {index} должен быть строкой")
    return DiskEntry(
        slot=slot,
        index=index,
        serial=serial.strip(),
        path_contains=path_contains.strip(),
        mount=mount.strip(),
    )


def _place(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > 4:
        raise LibraryError("config", f"{name} — целое от 1 до 4")
    return value
