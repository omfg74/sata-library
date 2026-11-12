import tomllib
from pathlib import Path

from sata_library.errors import LibraryError
from sata_library.model import Bay, LibraryConfig


def load_config(path: str | Path) -> LibraryConfig:
    try:
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise LibraryError("config", f"не читается {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise LibraryError("config", "файл манифеста не TOML") from exc

    raw_bays = data.get("bay")
    if not isinstance(raw_bays, list) or not raw_bays:
        raise LibraryError("config", "нужен хотя бы один [[bay]]")

    bays: list[Bay] = []
    seen: set[int] = set()
    for item in raw_bays:
        bay = _bay(item)
        if bay.id in seen:
            raise LibraryError("config", f"отсек {bay.id} указан дважды")
        seen.add(bay.id)
        bays.append(bay)

    path_contains = data.get("path_contains", "")
    if not isinstance(path_contains, str):
        raise LibraryError("config", "path_contains должен быть строкой")
    return LibraryConfig(path_contains=path_contains, bays=tuple(bays))


def _bay(item: object) -> Bay:
    if not isinstance(item, dict):
        raise LibraryError("config", "запись bay должна быть таблицей")
    raw_id = item.get("id")
    if not isinstance(raw_id, int) or raw_id < 1:
        raise LibraryError("config", "id отсека — целое от 1")
    serial = item.get("serial", "")
    if not isinstance(serial, str):
        raise LibraryError("config", f"серийник отсека {raw_id} должен быть строкой")
    return Bay(id=raw_id, serial=serial.strip())
