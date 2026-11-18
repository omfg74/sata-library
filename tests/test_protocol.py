import os
import threading
import tty
import unittest

from sata_library.errors import LibraryError
from sata_library.transport import LineTransport, MockTransport, SerialLink, parse_state


class Script:
    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.sent: list[str] = []

    def send(self, command: str) -> None:
        self.sent.append(command)

    def recv(self) -> str:
        return self.replies.pop(0)


class ProtocolTests(unittest.TestCase):
    def test_state_roundtrip(self) -> None:
        link = Script(
            [
                "OK state slots=0,0,0,0 present=1,0,0,0 disks=0,0,0,0",
                "OK slot 1 on",
            ]
        )
        transport = LineTransport(link)
        home = transport.state()
        transport.slot_on(1)
        self.assertEqual(home.slots, (False, False, False, False))
        self.assertEqual(home.present, (True, False, False, False))
        self.assertEqual(link.sent, ["STATE", "SLOT 1 ON"])

    def test_controller_error(self) -> None:
        link = Script(["ERR no_eeprom magic"])
        with self.assertRaises(LibraryError) as caught:
            LineTransport(link).slot_on(1)
        self.assertEqual(caught.exception.code, "no_eeprom")
        self.assertEqual(caught.exception.message, "magic")

    def test_old_carriage_state_is_rejected(self) -> None:
        with self.assertRaises(LibraryError) as caught:
            parse_state("OK state bay=1 z=mated power=1")
        self.assertEqual(caught.exception.code, "bad_reply")

    def test_bad_flags(self) -> None:
        with self.assertRaises(LibraryError) as caught:
            parse_state("OK state slots=1 present=1,0,0,0 disks=0,0,0,0")
        self.assertEqual(caught.exception.code, "bad_reply")


class MockInterlockTests(unittest.TestCase):
    def test_disk_before_slot_is_refused(self) -> None:
        transport = MockTransport()
        with self.assertRaises(LibraryError) as caught:
            transport.disk_on(1, 1)
        self.assertEqual(caught.exception.code, "slot_off")
        self.assertFalse(any(transport.disks))

    def test_second_slot_drops_the_first(self) -> None:
        transport = MockTransport()
        transport.slot_on(1)
        transport.disk_on(1, 1)
        transport.slot_on(2)
        self.assertEqual(transport.slots, [False, True, False, False])
        self.assertFalse(any(transport.disks))

    def test_bad_slot(self) -> None:
        transport = MockTransport()
        with self.assertRaises(LibraryError) as caught:
            transport.slot_on(0)
        self.assertEqual(caught.exception.code, "bad_arg")


class SerialTests(unittest.TestCase):
    def test_port_roundtrip(self) -> None:
        master, slave = os.openpty()
        name = os.ttyname(slave)
        tty.setraw(master)
        done = threading.Event()

        def serve() -> None:
            buf = b""
            while not done.is_set():
                try:
                    chunk = os.read(master, 64)
                except OSError:
                    return
                if chunk == b"":
                    return
                buf += chunk
                if b"\n" in buf:
                    os.write(master, b"OK pong\n")
                    return

        thread = threading.Thread(target=serve)
        thread.start()
        link = SerialLink(name, timeout_s=2)
        os.close(slave)
        try:
            link.send("PING")
            self.assertEqual(link.recv(), "OK pong")
        finally:
            link.close()
            done.set()
            os.close(master)
            thread.join(timeout=2)
