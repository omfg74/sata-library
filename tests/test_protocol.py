import unittest

from sata_library.errors import LibraryError
from sata_library.transport import LineTransport, MockTransport, parse_state


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
                "OK state bay=home z=retracted power=0",
                "OK state bay=2 z=mated power=1",
            ]
        )
        transport = LineTransport(link)
        home = transport.state()
        transport.seek(2)
        self.assertIsNone(home.bay)
        self.assertEqual(link.sent, ["STATE", "SEEK 2"])
        self.assertEqual(parse_state("OK state bay=2 z=mated power=1").power, True)

    def test_controller_error(self) -> None:
        link = Script(["ERR z_not_clear разъём не отведён"])
        with self.assertRaises(LibraryError) as caught:
            LineTransport(link).seek(1)
        self.assertEqual(caught.exception.code, "z_not_clear")
        self.assertEqual(caught.exception.message, "разъём не отведён")

    def test_bad_state(self) -> None:
        with self.assertRaises(LibraryError) as caught:
            parse_state("OK state bay=1 z=sideways power=0")
        self.assertEqual(caught.exception.code, "bad_reply")


class MockInterlockTests(unittest.TestCase):
    def test_power_before_mate_is_refused(self) -> None:
        transport = MockTransport()
        transport.seek(1)
        with self.assertRaises(LibraryError) as caught:
            transport.set_power(True)
        self.assertEqual(caught.exception.code, "not_mated")
        self.assertFalse(transport.power)

    def test_seek_while_mated_is_refused(self) -> None:
        transport = MockTransport()
        transport.seek(1)
        transport.mate()
        with self.assertRaises(LibraryError) as caught:
            transport.seek(2)
        self.assertEqual(caught.exception.code, "not_parked")
        self.assertEqual(transport.bay, 1)
