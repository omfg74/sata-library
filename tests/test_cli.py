import io
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
                ["backup", "--config", CONFIG, "--bay", "1", "--source", "/data", "--dry-run"]
            )
        self.assertEqual(code, 0)
        text = stdout.getvalue()
        self.assertIn("seek 1", text)
        self.assertIn("retract", text)
        self.assertIn("serial REPLACE-ME", text)

    def test_real_port_is_not_wired(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = main(["backup", "--config", CONFIG, "--bay", "1", "--source", "/data"])
        self.assertEqual(code, 1)
        self.assertIn("not_connected", stderr.getvalue())

    def test_identify_dry_run(self) -> None:
        with redirect_stdout(io.StringIO()):
            code = main(["identify", "--config", CONFIG, "--bay", "1", "--dry-run"])
        self.assertEqual(code, 0)
