import tempfile
import unittest
from pathlib import Path

from sata_library.config import load_config
from sata_library.errors import LibraryError
from sata_library.machine import Library, RecordingCopier, RsyncCopier
from sata_library.model import Disk, DiskEntry, LibraryConfig
from sata_library.transport import MockTransport


ROOT = Path(__file__).resolve().parents[1]


class ManualClock:
    def __init__(self) -> None:
        self.t = 0.0
        self.slept: list[float] = []

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.t += seconds


def disk(serial: str, path: str = "/dev/disk/by-path/library") -> Disk:
    return Disk(name="sda", serial=serial, wwn="0x1", size="4T", tran="usb", path=path)


def entry(
    slot: int = 1,
    index: int = 1,
    serial: str = "WD-1",
    path: str = "library",
    mount: str = "/mnt/shelf",
) -> DiskEntry:
    return DiskEntry(slot, index, serial, path, mount)


def library(
    transport: MockTransport,
    disks: list[Disk],
    copier: RecordingCopier | None = None,
    serial: str = "WD-1",
    path: str = "library",
    dry_run: bool = False,
) -> tuple[Library, ManualClock]:
    config = LibraryConfig(8, (entry(serial=serial, path=path),))
    clock = ManualClock()
    lib = Library(
        transport,
        config,
        lambda: disks,
        copier or RecordingCopier(),
        sleeper=clock.sleep,
        clock=clock.now,
        dry_run=dry_run,
    )
    return lib, clock


class BackupTests(unittest.TestCase):
    def test_happy_path_powers_one_disk_and_copies(self) -> None:
        transport = MockTransport()
        copier = RecordingCopier()
        lib, clock = library(transport, [disk("WD-1")], copier)
        found = lib.backup(1, 1, "/data")

        self.assertEqual(found.serial, "WD-1")
        self.assertEqual(copier.calls, [("/data", "WD-1")])
        self.assertEqual(
            transport.commands,
            ["SLOT 1 ON", "DISK 1 1 ON", "DISK 1 1 OFF", "SLOT 1 OFF"],
        )
        self.assertEqual(clock.slept, [])
        self.assertFalse(any(transport.slots))
        self.assertFalse(any(transport.disks))

    def test_second_disk_waits_eight_seconds(self) -> None:
        transport = MockTransport()
        lib, clock = library(transport, [disk("WD-1")])
        lib._ensure_slot(1)
        lib._ensure_disk(1, 1)
        lib._ensure_disk(1, 2)

        self.assertEqual(clock.slept, [8])
        self.assertEqual(transport.disks, [True, True, False, False])

    def test_empty_manifest_does_not_power(self) -> None:
        transport = MockTransport()
        lib, _clock = library(transport, [disk("WD-1")], serial="")
        with self.assertRaises(LibraryError) as caught:
            lib.backup(1, 1, "/data")
        self.assertEqual(caught.exception.code, "unknown_disk")
        self.assertEqual(transport.commands, [])

    def test_empty_filter_on_a_live_run_does_not_power(self) -> None:
        transport = MockTransport()
        lib, _clock = library(transport, [disk("WD-1")], path="")
        with self.assertRaises(LibraryError) as caught:
            lib.backup(1, 1, "/data")
        self.assertEqual(caught.exception.code, "path_filter")
        self.assertEqual(transport.commands, [])

    def test_dry_run_allows_an_empty_filter(self) -> None:
        transport = MockTransport()
        lib, _clock = library(transport, [disk("WD-1", "dry-run")], path="", dry_run=True)
        found = lib.identify(1, 1)
        self.assertEqual(found.serial, "WD-1")

    def test_serial_mismatch_powers_off_without_copy(self) -> None:
        transport = MockTransport()
        copier = RecordingCopier()
        lib, _clock = library(transport, [disk("OTHER")], copier)
        with self.assertRaises(LibraryError) as caught:
            lib.backup(1, 1, "/data")
        self.assertEqual(caught.exception.code, "serial_mismatch")
        self.assertEqual(copier.calls, [])
        self.assertFalse(any(transport.slots))
        self.assertFalse(transport.fault)

    def test_copy_failure_still_powers_off(self) -> None:
        transport = MockTransport()
        lib, _clock = library(transport, [disk("WD-1")], RecordingCopier(fail=True))
        with self.assertRaises(LibraryError) as caught:
            lib.backup(1, 1, "/data")
        self.assertEqual(caught.exception.code, "copy_failed")
        self.assertFalse(any(transport.slots))
        self.assertFalse(any(transport.disks))

    def test_release_failure_stops_the_controller(self) -> None:
        transport = MockTransport()
        transport.fail_release = True
        lib, _clock = library(transport, [disk("WD-1")])
        with self.assertRaises(LibraryError) as caught:
            lib.backup(1, 1, "/data")
        self.assertEqual(caught.exception.code, "i2c")
        self.assertTrue(transport.fault)
        self.assertFalse(any(transport.slots))
        self.assertIn("ESTOP", transport.commands)

    def test_missing_eeprom_leaves_the_slot_off(self) -> None:
        transport = MockTransport()
        transport.eeprom[0] = False
        lib, _clock = library(transport, [disk("WD-1")])
        with self.assertRaises(LibraryError) as caught:
            lib.backup(1, 1, "/data")
        self.assertEqual(caught.exception.code, "no_eeprom")
        self.assertFalse(any(transport.slots))
        self.assertNotIn("DISK 1 1 ON", transport.commands)

    def test_absent_board_is_not_powered(self) -> None:
        transport = MockTransport()
        transport.present[0] = False
        lib, _clock = library(transport, [disk("WD-1")])
        with self.assertRaises(LibraryError) as caught:
            lib.backup(1, 1, "/data")
        self.assertEqual(caught.exception.code, "not_present")
        self.assertEqual(transport.commands, [])

    def test_waits_until_the_disk_appears(self) -> None:
        transport = MockTransport()
        calls = {"n": 0}

        def source() -> list[Disk]:
            calls["n"] += 1
            if calls["n"] < 3:
                return []
            return [disk("WD-1")]

        config = LibraryConfig(8, (entry(),))
        clock = ManualClock()
        lib = Library(
            transport,
            config,
            source,
            RecordingCopier(),
            sleeper=clock.sleep,
            clock=clock.now,
        )
        found = lib.backup(1, 1, "/data")
        self.assertEqual(found.serial, "WD-1")
        self.assertEqual(clock.slept, [0.25, 0.25])

    def test_gives_up_when_the_disk_never_appears(self) -> None:
        transport = MockTransport()
        config = LibraryConfig(8, (entry(),))
        clock = ManualClock()
        lib = Library(
            transport,
            config,
            lambda: [],
            RecordingCopier(),
            sleeper=clock.sleep,
            clock=clock.now,
            ready_s=0.5,
        )
        with self.assertRaises(LibraryError) as caught:
            lib.backup(1, 1, "/data")
        self.assertEqual(caught.exception.code, "disk_count")
        self.assertFalse(any(transport.slots))

    def test_identify_returns_whatever_serial_is_there(self) -> None:
        lib, _clock = library(MockTransport(), [disk("OTHER")])
        self.assertEqual(lib.identify(1, 1).serial, "OTHER")

    def test_two_disks_abort(self) -> None:
        transport = MockTransport()
        lib, _clock = library(
            transport,
            [disk("A"), disk("B", "/dev/disk/by-path/library-b")],
        )
        with self.assertRaises(LibraryError) as caught:
            lib.identify(1, 1)
        self.assertEqual(caught.exception.code, "disk_count")
        self.assertFalse(any(transport.slots))

    def test_filter_ignores_other_paths(self) -> None:
        lib, _clock = library(MockTransport(), [disk("WD-1"), disk("NOISE", "/dev/sda")])
        self.assertEqual(lib.identify(1, 1).serial, "WD-1")

    def test_missing_disk(self) -> None:
        lib, _clock = library(MockTransport(), [disk("WD-1")])
        with self.assertRaises(LibraryError) as caught:
            lib.identify(2, 1)
        self.assertEqual(caught.exception.code, "bad_disk")


class RsyncTests(unittest.TestCase):
    def test_empty_mount_does_not_start_rsync(self) -> None:
        started = {"yes": False}

        def run(*_args, **_kwargs):
            started["yes"] = True
            raise AssertionError("rsync не должен стартовать")

        with self.assertRaises(LibraryError) as caught:
            RsyncCopier(run).copy("/data", disk("WD-1"), "")
        self.assertEqual(caught.exception.code, "no_mount")
        self.assertFalse(started["yes"])

    def test_rsync_error_is_visible(self) -> None:
        def run(cmd, check, capture_output, text):
            self.assertEqual(cmd, ["rsync", "-a", "--", "/data/", "/mnt/shelf/"])
            self.assertFalse(check)
            return subprocess_result(cmd, "permission denied")

        with self.assertRaises(LibraryError) as caught:
            RsyncCopier(run).copy("/data", disk("WD-1"), "/mnt/shelf")
        self.assertEqual(caught.exception.code, "copy_failed")
        self.assertEqual(caught.exception.message, "permission denied")


def subprocess_result(cmd, stderr: str):
    import subprocess

    return subprocess.CompletedProcess(cmd, 1, "", stderr)


class ConfigTests(unittest.TestCase):
    def test_example_manifest(self) -> None:
        config = load_config(ROOT / "config" / "library.example.toml")
        self.assertEqual(config.spin_pause_s, 8)
        self.assertEqual(
            config.disks,
            (DiskEntry(1, 1, "REPLACE-ME", "", ""),),
        )

    def test_duplicate_disk(self) -> None:
        text = (ROOT / "config" / "library.example.toml").read_text(encoding="utf-8")
        text += "\n[[disk]]\nslot = 1\nindex = 1\nserial = \"X\"\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dup.toml"
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(LibraryError) as caught:
                load_config(path)
        self.assertEqual(caught.exception.code, "config")
