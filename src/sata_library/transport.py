import os
import select
import termios
import time
import tty
from typing import Protocol

from sata_library.errors import LibraryError
from sata_library.model import ShelfState

_BAUD = 115200


class Transport(Protocol):
    def state(self) -> ShelfState: ...

    def estop(self) -> None: ...

    def slot_on(self, slot: int) -> None: ...

    def slot_off(self, slot: int) -> None: ...

    def disk_on(self, slot: int, index: int) -> None: ...

    def disk_off(self, slot: int, index: int) -> None: ...


class Link(Protocol):
    def send(self, command: str) -> None: ...

    def recv(self) -> str: ...


class MockTransport:
    """Контроллер в памяти. Те же запреты, что в прошивке: один слот, диск только на включённом слоте."""

    def __init__(self) -> None:
        self.slots = [False, False, False, False]
        self.present = [True, True, True, True]
        self.eeprom = [True, True, True, True]
        self.disks = [False, False, False, False]
        self.fault = False
        self.fail_release = False
        self.commands: list[str] = []

    def state(self) -> ShelfState:
        return ShelfState(tuple(self.slots), tuple(self.present), tuple(self.disks))

    def estop(self) -> None:
        self.fault = True
        self.slots = [False, False, False, False]
        self.disks = [False, False, False, False]
        self.commands.append("ESTOP")

    def slot_on(self, slot: int) -> None:
        self._ready()
        _place(slot)
        if not self.present[slot - 1]:
            raise LibraryError("not_present", "absent")
        self.slots = [False, False, False, False]
        self.disks = [False, False, False, False]
        self.slots[slot - 1] = True
        self.commands.append(f"SLOT {slot} ON")
        if not self.eeprom[slot - 1]:
            self.slots[slot - 1] = False
            raise LibraryError("no_eeprom", "magic")

    def slot_off(self, slot: int) -> None:
        self._ready()
        _place(slot)
        if self.slots[slot - 1]:
            self.slots[slot - 1] = False
            self.disks = [False, False, False, False]
        self.commands.append(f"SLOT {slot} OFF")

    def disk_on(self, slot: int, index: int) -> None:
        self._disk(slot, index, True)

    def disk_off(self, slot: int, index: int) -> None:
        self._disk(slot, index, False)

    def _disk(self, slot: int, index: int, on: bool) -> None:
        self._ready()
        _place(slot)
        _place(index)
        if not self.slots[slot - 1]:
            raise LibraryError("slot_off", "off")
        if not on and self.fail_release:
            self.commands.append(f"DISK {slot} {index} OFF")
            raise LibraryError("i2c", "fail")
        self.disks[index - 1] = on
        self.commands.append(f"DISK {slot} {index} {'ON' if on else 'OFF'}")

    def _ready(self) -> None:
        if self.fault:
            raise LibraryError("fault", "контроллер в аварии")


class LineTransport:
    """Текстовый протокол hardware/INTERFACE.md. Поток — порт или подстановка теста."""

    def __init__(self, link: Link) -> None:
        self.link = link

    def state(self) -> ShelfState:
        return parse_state(self._roundtrip("STATE"))

    def estop(self) -> None:
        self._roundtrip("ESTOP")

    def slot_on(self, slot: int) -> None:
        self._roundtrip(f"SLOT {slot} ON")

    def slot_off(self, slot: int) -> None:
        self._roundtrip(f"SLOT {slot} OFF")

    def disk_on(self, slot: int, index: int) -> None:
        self._roundtrip(f"DISK {slot} {index} ON")

    def disk_off(self, slot: int, index: int) -> None:
        self._roundtrip(f"DISK {slot} {index} OFF")

    def _roundtrip(self, command: str) -> str:
        self.link.send(command)
        reply = self.link.recv().strip()
        if reply.startswith("ERR "):
            rest = reply[4:]
            code, _, message = rest.partition(" ")
            raise LibraryError(code or "controller", message or rest)
        if not reply.startswith("OK"):
            raise LibraryError("bad_reply", reply or "пустой ответ")
        return reply


class SerialLink:
    """UART 115200 8N1. Ответ — одна строка, без неё это ошибка, не пустой успех."""

    def __init__(self, port: str, timeout_s: float = 2.0) -> None:
        try:
            self._fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_CLOEXEC)
        except OSError as exc:
            raise LibraryError("not_connected", f"не открывается {port}") from exc
        self._timeout = timeout_s
        self._buf = b""
        try:
            self._configure()
        except Exception:
            os.close(self._fd)
            raise

    def close(self) -> None:
        os.close(self._fd)

    def send(self, command: str) -> None:
        os.write(self._fd, (command + "\n").encode())

    def recv(self) -> str:
        deadline = time.monotonic() + self._timeout
        while b"\n" not in self._buf:
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise LibraryError("no_reply", "контроллер не ответил")
            ready, _, _ = select.select([self._fd], [], [], remain)
            if not ready:
                raise LibraryError("no_reply", "контроллер не ответил")
            try:
                chunk = os.read(self._fd, 128)
            except OSError as exc:
                raise LibraryError("not_connected", "порт оборвался") from exc
            if chunk == b"":
                raise LibraryError("no_reply", "порт закрылся")
            self._buf += chunk
        line, _, self._buf = self._buf.partition(b"\n")
        try:
            return line.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise LibraryError("bad_reply", "ответ не UTF-8") from exc

    def _configure(self) -> None:
        tty.setraw(self._fd)
        attr = termios.tcgetattr(self._fd)
        attr[4] = termios.B115200
        attr[5] = termios.B115200
        termios.tcsetattr(self._fd, termios.TCSANOW, attr)
        os.set_blocking(self._fd, False)


def parse_state(reply: str) -> ShelfState:
    parts = reply.split()
    if len(parts) != 5 or parts[0] != "OK" or parts[1] != "state":
        raise LibraryError("bad_reply", reply)
    fields: dict[str, str] = {}
    for part in parts[2:]:
        key, separator, value = part.partition("=")
        if separator != "=" or key == "":
            raise LibraryError("bad_reply", reply)
        fields[key] = value
    try:
        return ShelfState(
            slots=_flags(fields["slots"], reply),
            present=_flags(fields["present"], reply),
            disks=_flags(fields["disks"], reply),
        )
    except KeyError as exc:
        raise LibraryError("bad_reply", reply) from exc


def _flags(text: str, reply: str) -> tuple[bool, bool, bool, bool]:
    parts = text.split(",")
    if len(parts) != 4 or any(part not in {"0", "1"} for part in parts):
        raise LibraryError("bad_reply", reply)
    return (parts[0] == "1", parts[1] == "1", parts[2] == "1", parts[3] == "1")


def _place(number: int) -> None:
    if number < 1 or number > 4:
        raise LibraryError("bad_arg", "range")
