import argparse
import subprocess
import sys
from pathlib import Path

from sata_library.disks import LSBLK_COLUMNS, disks_from_lsblk
from sata_library.errors import LibraryError
from sata_library.machine import Library, RecordingCopier
from sata_library.model import Disk
from sata_library.config import load_config
from sata_library.transport import MockTransport


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sata-library")
    commands = parser.add_subparsers(dest="cmd", required=True)

    backup = commands.add_parser("backup", help="стыковка и копирование")
    _add_job_args(backup, source=True)

    identify = commands.add_parser("identify", help="прочитать серийник в отсеке")
    _add_job_args(identify, source=False)

    listing = commands.add_parser("disks", help="показать диски из lsblk")
    listing.add_argument("--json-file", help="готовый JSON lsblk -J вместо живого вызова")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "disks":
            _print_disks(args.json_file)
        elif args.cmd == "backup":
            _run_backup(args)
        else:
            _run_identify(args)
    except LibraryError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        return 1
    return 0


def _add_job_args(parser: argparse.ArgumentParser, source: bool) -> None:
    parser.add_argument("--config", required=True)
    parser.add_argument("--bay", required=True, type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--disks-json", help="JSON lsblk вместо опроса ядра")
    if source:
        parser.add_argument("--source", required=True)


def _run_backup(args: argparse.Namespace) -> None:
    _require_dry_run(args.dry_run)
    config = load_config(args.config)
    bay = next((item for item in config.bays if item.id == args.bay), None)
    if bay is None:
        raise LibraryError("bad_bay", f"отсека {args.bay} нет в манифесте")
    disks, note = _disk_source(args.disks_json, bay.serial or "DRY-RUN")
    transport = MockTransport()
    library = Library(transport, config, lambda: disks, RecordingCopier())
    disk = library.backup(args.bay, args.source)
    _print_trace(transport, disk, note, config.path_contains)


def _run_identify(args: argparse.Namespace) -> None:
    _require_dry_run(args.dry_run)
    config = load_config(args.config)
    disks, note = _disk_source(args.disks_json, "DRY-RUN")
    transport = MockTransport()
    library = Library(transport, config, lambda: disks, RecordingCopier())
    disk = library.identify(args.bay)
    _print_trace(transport, disk, note, config.path_contains)


def _require_dry_run(enabled: bool) -> None:
    if not enabled:
        raise LibraryError(
            "not_connected",
            "порт контроллера ещё не подключён, сейчас работает --dry-run",
        )


def _disk_source(json_path: str | None, synthetic_serial: str) -> tuple[list[Disk], str]:
    if json_path:
        return disks_from_lsblk(Path(json_path).read_text(encoding="utf-8")), ""
    disk = Disk(
        name="dry",
        serial=synthetic_serial,
        wwn="",
        size="0",
        tran="dry-run",
        path="dry-run",
    )
    return [disk], "диск подставлен из аргументов, полка не читалась"


def _print_trace(transport: MockTransport, disk: Disk, note: str, path_contains: str) -> None:
    if note:
        print(note)
    if path_contains == "":
        print("фильтр порта пустой")
    for command in transport.commands:
        print(command)
    print(f"serial {disk.serial}")


def _print_disks(json_path: str | None) -> None:
    if json_path:
        payload = Path(json_path).read_text(encoding="utf-8")
    else:
        payload = _lsblk()
    for disk in disks_from_lsblk(payload):
        print(f"{disk.name}\t{disk.serial}\t{disk.tran}\t{disk.path}")


def _lsblk() -> str:
    try:
        result = subprocess.run(
            ["lsblk", "-J", "-o", LSBLK_COLUMNS],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LibraryError("lsblk", "не удалось вызвать lsblk") from exc
    return result.stdout
