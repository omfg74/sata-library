from typing import Protocol

from sata_library.errors import LibraryError
from sata_library.model import Snapshot

_Z = {"retracted", "between", "mated"}


class Transport(Protocol):
    def state(self) -> Snapshot: ...

    def estop(self) -> None: ...

    def home(self) -> None: ...

    def seek(self, bay_id: int) -> None: ...

    def mate(self) -> None: ...

    def retract(self) -> None: ...

    def set_power(self, on: bool) -> None: ...


class Link(Protocol):
    def send(self, command: str) -> None: ...

    def recv(self) -> str: ...


class MockTransport:
    """Контроллер в памяти. Повторяет те же запреты, что должны быть в прошивке."""

    def __init__(self) -> None:
        self.bay: int | None = None
        self.z = "retracted"
        self.power = False
        self.fault = False
        self.fail_retract = False
        self.commands: list[str] = []

    def state(self) -> Snapshot:
        return Snapshot(self.bay, self.z, self.power)

    def estop(self) -> None:
        self.fault = True
        self.power = False
        self.commands.append("estop")

    def home(self) -> None:
        self._ready()
        self._require_parked("домой только с отведённым разъёмом и без питания")
        self.bay = None
        self.commands.append("home")

    def seek(self, bay_id: int) -> None:
        self._ready()
        self._require_parked("перед ходом выбора разъём должен быть отведён, питание выключено")
        if bay_id < 1:
            raise LibraryError("bad_bay", "номер отсека начинается с 1")
        self.bay = bay_id
        self.commands.append(f"seek {bay_id}")

    def mate(self) -> None:
        self._ready()
        if self.bay is None:
            raise LibraryError("not_aligned", "стыковка не на отсеке")
        if self.power:
            raise LibraryError("power_on", "стыковка при включённом питании")
        self.z = "mated"
        self.commands.append("mate")

    def retract(self) -> None:
        self._ready()
        if self.power:
            raise LibraryError("power_on", "нельзя отводить разъём под питанием")
        self.commands.append("retract")
        if self.fail_retract:
            self.z = "between"
            raise LibraryError("retract_failed", "концевик отведённого разъёма не сработал")
        self.z = "retracted"

    def set_power(self, on: bool) -> None:
        self._ready()
        if on and self.z != "mated":
            raise LibraryError("not_mated", "питание только после стыковки")
        self.power = bool(on)
        self.commands.append(f"power {1 if self.power else 0}")

    def _ready(self) -> None:
        if self.fault:
            raise LibraryError("fault", "контроллер в аварии")

    def _require_parked(self, message: str) -> None:
        if self.z != "retracted" or self.power:
            raise LibraryError("not_parked", message)


class LineTransport:
    """Текстовый протокол к контроллеру. Поток подставляет тест или будущий порт."""

    def __init__(self, link: Link) -> None:
        self.link = link

    def state(self) -> Snapshot:
        return parse_state(self._roundtrip("STATE"))

    def estop(self) -> None:
        self._roundtrip("ESTOP")

    def home(self) -> None:
        self._roundtrip("HOME")

    def seek(self, bay_id: int) -> None:
        self._roundtrip(f"SEEK {bay_id}")

    def mate(self) -> None:
        self._roundtrip("MATE")

    def retract(self) -> None:
        self._roundtrip("RETRACT")

    def set_power(self, on: bool) -> None:
        self._roundtrip(f"POWER {1 if on else 0}")

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


def parse_state(reply: str) -> Snapshot:
    parts = reply.split()
    if len(parts) < 5 or parts[0] != "OK" or parts[1] != "state":
        raise LibraryError("bad_reply", reply)
    fields: dict[str, str] = {}
    for part in parts[2:]:
        key, separator, value = part.partition("=")
        if separator != "=" or key == "":
            raise LibraryError("bad_reply", reply)
        fields[key] = value
    try:
        bay_text = fields["bay"]
        z = fields["z"]
        power_text = fields["power"]
    except KeyError as exc:
        raise LibraryError("bad_reply", reply) from exc
    if z not in _Z:
        raise LibraryError("bad_reply", reply)
    if power_text not in {"0", "1"}:
        raise LibraryError("bad_reply", reply)
    if bay_text == "home":
        bay = None
    else:
        try:
            bay = int(bay_text)
        except ValueError as exc:
            raise LibraryError("bad_reply", reply) from exc
        if bay < 1:
            raise LibraryError("bad_reply", reply)
    return Snapshot(bay=bay, z=z, power=power_text == "1")
