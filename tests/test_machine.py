import tempfile
import unittest
from pathlib import Path

from sata_library.config import load_config
from sata_library.errors import LibraryError
from sata_library.machine import Library, RecordingCopier
from sata_library.model import Bay, Disk, LibraryConfig
from sata_library.transport import MockTransport

ROOT = Path(__file__).resolve().parents[1]


def disk(serial: str, path: str = "/dev/disk/by-path/library") -> Disk:
    return Disk(name="sda", serial=serial, wwn="0x1", size="4T", tran="usb", path=path)


def library(transport: MockTransport, disks: list[Disk], copier: RecordingCopier | None = None, serial: str = "WD-1") -> Library:
    config = LibraryConfig(path_contains="library", bays=(Bay(1, serial),))
    return Library(transport, config, lambda: disks, copier or RecordingCopier())


class BackupTests(unittest.TestCase):
    def test_happy_path_parks_and_copies(self) -> None:
        transport = MockTransport()
        copier = RecordingCopier()
        found = library(transport, [disk("WD-1")], copier).backup(1, "/data")

        self.assertEqual(found.serial, "WD-1")
        self.assertEqual(copier.calls, [("/data", "WD-1")])
        self.assertEqual(transport.commands, ["seek 1", "mate", "power 1", "power 0", "retract"])
        self.assertEqual(transport.z, "retracted")
        self.assertFalse(transport.power)

    def test_skips_seek_when_already_on_the_bay(self) -> None:
        transport = MockTransport()
        transport.bay = 1
        library(transport, [disk("WD-1")]).backup(1, "/data")
        self.assertNotIn("seek 1", transport.commands)

    def test_empty_manifest_does_not_move(self) -> None:
        transport = MockTransport()
        with self.assertRaises(LibraryError) as caught:
            library(transport, [disk("WD-1")], serial="").backup(1, "/data")
        self.assertEqual(caught.exception.code, "unknown_disk")
        self.assertEqual(transport.commands, [])

    def test_serial_mismatch_parks_without_copy(self) -> None:
        transport = MockTransport()
        copier = RecordingCopier()
        with self.assertRaises(LibraryError) as caught:
            library(transport, [disk("OTHER")], copier).backup(1, "/data")
        self.assertEqual(caught.exception.code, "serial_mismatch")
        self.assertEqual(copier.calls, [])
        self.assertEqual(transport.z, "retracted")
        self.assertFalse(transport.power)
        self.assertFalse(transport.fault)

    def test_copy_failure_still_parks(self) -> None:
        transport = MockTransport()
        copier = RecordingCopier(fail=True)
        with self.assertRaises(LibraryError) as caught:
            library(transport, [disk("WD-1")], copier).backup(1, "/data")
        self.assertEqual(caught.exception.code, "copy_failed")
        self.assertEqual(transport.z, "retracted")
        self.assertFalse(transport.power)

    def test_retract_failure_stops_the_controller(self) -> None:
        transport = MockTransport()
        transport.fail_retract = True
        with self.assertRaises(LibraryError) as caught:
            library(transport, [disk("WD-1")]).backup(1, "/data")
        self.assertEqual(caught.exception.code, "retract_failed")
        self.assertTrue(transport.fault)
        self.assertFalse(transport.power)
        self.assertEqual(transport.z, "between")
        self.assertIn("estop", transport.commands)

    def test_refuses_to_travel_while_mated(self) -> None:
        transport = MockTransport()
        transport.z = "mated"
        transport.bay = 1
        with self.assertRaises(LibraryError) as caught:
            library(transport, [disk("WD-1")]).backup(1, "/data")
        self.assertEqual(caught.exception.code, "not_parked")
        self.assertEqual(transport.commands, [])

    def test_identify_returns_whatever_serial_is_there(self) -> None:
        found = library(MockTransport(), [disk("OTHER")], serial="WD-1").identify(1)
        self.assertEqual(found.serial, "OTHER")

    def test_two_disks_abort(self) -> None:
        transport = MockTransport()
        with self.assertRaises(LibraryError) as caught:
            library(transport, [disk("A"), disk("B", "/dev/disk/by-path/library-b")]).identify(1)
        self.assertEqual(caught.exception.code, "disk_count")
        self.assertEqual(transport.z, "retracted")

    def test_filter_ignores_other_paths(self) -> None:
        disks = [disk("WD-1"), disk("NOISE", "/dev/sda")]
        found = library(MockTransport(), disks).identify(1)
        self.assertEqual(found.serial, "WD-1")

    def test_missing_bay(self) -> None:
        with self.assertRaises(LibraryError) as caught:
            library(MockTransport(), [disk("WD-1")]).identify(4)
        self.assertEqual(caught.exception.code, "bad_bay")


class ConfigTests(unittest.TestCase):
    def test_example_manifest(self) -> None:
        config = load_config(ROOT / "config" / "library.example.toml")
        self.assertEqual(config.bays, (Bay(1, "REPLACE-ME"),))
        self.assertEqual(config.path_contains, "")

    def test_duplicate_bay(self) -> None:
        text = (ROOT / "config" / "library.example.toml").read_text(encoding="utf-8")
        text += "\n[[bay]]\nid = 1\nserial = \"X\"\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dup.toml"
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(LibraryError) as caught:
                load_config(path)
        self.assertEqual(caught.exception.code, "config")
