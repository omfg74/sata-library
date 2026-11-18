import io
import json
import os
import tempfile
import threading
import tty
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from sata_library.cli import main

ROOT = Path(__file__).resolve().parents[1]
CONFIG = str(ROOT / "config" / "library.example.toml")


class CliTests(unittest.TestCase):
    def test_dry_run_prints_the_sequence(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(
                [
                    "backup",
                    "--config",
                    CONFIG,
                    "--slot",
                    "1",
                    "--disk",
                    "1",
                    "--source",
                    "/data",
                    "--dry-run",
                ]
            )
        self.assertEqual(code, 0)
        text = stdout.getvalue()
        self.assertIn("SLOT 1 ON", text)
        self.assertIn("DISK 1 1 ON", text)
        self.assertIn("DISK 1 1 OFF", text)
        self.assertIn("SLOT 1 OFF", text)
        self.assertIn("serial REPLACE-ME", text)
        self.assertNotIn("seek", text)

    def test_live_run_without_port_stops(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = main(
                ["backup", "--config", CONFIG, "--slot", "1", "--disk", "1", "--source", "/data"]
            )
        self.assertEqual(code, 1)
        self.assertIn("not_connected", stderr.getvalue())

    def test_identify_dry_run(self) -> None:
        with redirect_stdout(io.StringIO()):
            code = main(["identify", "--config", CONFIG, "--slot", "1", "--disk", "1", "--dry-run"])
        self.assertEqual(code, 0)

    def test_live_port_powers_the_slot_and_stops_on_the_serial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            config = folder / "library.toml"
            config.write_text(
                "\n".join(
                    [
                        "spin_pause_s = 8",
                        "[[disk]]",
                        "slot = 1",
                        "index = 1",
                        'serial = "WD-1"',
                        'path_contains = "usb-jms"',
                        'mount = "/mnt/shelf"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            listing = folder / "lsblk.json"
            listing.write_text(
                json.dumps(
                    {
                        "blockdevices": [
                            {
                                "name": "sda",
                                "serial": "OTHER",
                                "wwn": "",
                                "size": "4T",
                                "type": "disk",
                                "tran": "usb",
                                "path": "/dev/disk/by-path/usb-jms-1",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            master, slave = os.openpty()
            name = os.ttyname(slave)
            tty.setraw(master)
            seen: list[str] = []

            def serve() -> None:
                slots = [0, 0, 0, 0]
                disks = [0, 0, 0, 0]
                buf = b""
                while True:
                    try:
                        chunk = os.read(master, 128)
                    except OSError:
                        return
                    if chunk == b"":
                        return
                    buf += chunk
                    while b"\n" in buf:
                        raw, _, buf = buf.partition(b"\n")
                        line = raw.decode().strip()
                        seen.append(line)
                        os.write(master, (answer(line, slots, disks) + "\n").encode())

            thread = threading.Thread(target=serve)
            thread.start()
            stderr = io.StringIO()
            try:
                with redirect_stderr(stderr):
                    code = main(
                        [
                            "backup",
                            "--config",
                            str(config),
                            "--slot",
                            "1",
                            "--disk",
                            "1",
                            "--source",
                            "/data",
                            "--port",
                            name,
                            "--disks-json",
                            str(listing),
                        ]
                    )
            finally:
                os.close(slave)
                os.close(master)
                thread.join(timeout=2)
        self.assertEqual(code, 1)
        self.assertIn("serial_mismatch", stderr.getvalue())
        self.assertIn("SLOT 1 ON", seen)
        self.assertIn("DISK 1 1 ON", seen)
        self.assertIn("SLOT 1 OFF", seen)


def answer(line: str, slots: list[int], disks: list[int]) -> str:
    parts = line.split()
    if parts == ["STATE"]:
        slot_text = ",".join(str(item) for item in slots)
        disk_text = ",".join(str(item) for item in disks)
        return f"OK state slots={slot_text} present=1,0,0,0 disks={disk_text}"
    if len(parts) == 3 and parts[0] == "SLOT" and parts[2] == "ON":
        slots[:] = [0, 0, 0, 0]
        disks[:] = [0, 0, 0, 0]
        slots[int(parts[1]) - 1] = 1
        return f"OK slot {parts[1]} on"
    if len(parts) == 3 and parts[0] == "SLOT" and parts[2] == "OFF":
        if slots[int(parts[1]) - 1]:
            disks[:] = [0, 0, 0, 0]
        slots[int(parts[1]) - 1] = 0
        return f"OK slot {parts[1]} off"
    if len(parts) == 4 and parts[0] == "DISK" and parts[3] == "ON":
        disks[int(parts[2]) - 1] = 1
        return f"OK disk {parts[1]} {parts[2]} on"
    if len(parts) == 4 and parts[0] == "DISK" and parts[3] == "OFF":
        disks[int(parts[2]) - 1] = 0
        return f"OK disk {parts[1]} {parts[2]} off"
    return "ERR bad_arg command"
