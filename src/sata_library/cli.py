import argparse
import subprocess
import sys
from pathlib import Path

from sata_library.config import load_config
from sata_library.disks import LSBLK_COLUMNS, disks_from_lsblk
from sata_library.errors import LibraryError
from sata_library.machine import Library, RecordingCopier, RsyncCopier
from sata_library.model import Disk, DiskEntry, LibraryConfig
from sata_library.transport import LineTransport, MockTransport, SerialLink


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sata-library")
    commands = parser.add_subparsers(dest="cmd", required=True)

    backup = commands.add_parser("backup", help="включить диск и скопировать")
    _add_job_args(backup, source=True)

    identify = commands.add_parser("identify", help="прочитать серийник диска")
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
    parser.add_argument("--slot", required=True, type=int)
    parser.add_argument("--disk", required=True, type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--port", help="UART контроллера, например /dev/ttyUSB0")
    parser.add_argument("--disks-json", help="JSON lsblk вместо опроса ядра")
    if source:
        parser.add_argument("--source", required=True)


def _run_backup(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    entry = _require_entry(config, args.slot, args.disk)
    transport, dry = _open_transport(args)
    try:
        source_fn, note, copier = _job_parts(args, dry, entry.serial or "DRY-RUN")
        library = Library(transport, config, source_fn, copier, dry_run=dry)
        disk = library.backup(args.slot, args.disk, args.source)
        if dry:
            _print_trace(transport, disk, note, entry.path_contains)
        else:
            print(f"serial {disk.serial}")
    finally:
        _close(transport)


def _run_identify(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    entry = _require_entry(config, args.slot, args.disk)
    transport, dry = _open_transport(args)
    try:
        source_fn, note, copier = _job_parts(args, dry, "DRY-RUN")
        library = Library(transport, config, source_fn, copier, dry_run=dry)
        disk = library.identify(args.slot, args.disk)
        if dry:
            _print_trace(transport, disk, note, entry.path_contains)
        else:
            print(f"serial {disk.serial}")
    finally:
        _close(transport)


def _require_entry(config: LibraryConfig, slot: int, index: int) -> DiskEntry:
    for entry in config.disks:
        if entry.slot == slot and entry.index == index:
            return entry
    raise LibraryError("bad_disk", f"слота {slot} диска {index} нет в манифесте")


def _open_transport(args: argparse.Namespace) -> tuple[MockTransport | LineTransport, bool]:
    if args.dry_run:
        return MockTransport(), True
    if not args.port:
        raise LibraryError("not_connected", "нужен --port, например /dev/ttyUSB0")
    return LineTransport(SerialLink(args.port)), False


def _close(transport: MockTransport | LineTransport) -> None:
    link = getattr(transport, "link", None)
    if isinstance(link, SerialLink):
        link.close()


def _job_parts(args: argparse.Namespace, dry: bool, synthetic_serial: str):
    if dry:
        disks, note = _disk_source(args.disks_json, synthetic_serial)
        return (lambda: disks), note, RecordingCopier()
    note = ""
    if args.disks_json:
        payload = Path(args.disks_json).read_text(encoding="utf-8")
        return (lambda: disks_from_lsblk(payload)), note, RsyncCopier()
    return (lambda: disks_from_lsblk(_lsblk())), note, RsyncCopier()


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
