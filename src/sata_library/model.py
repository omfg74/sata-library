from dataclasses import dataclass


@dataclass(frozen=True)
class Disk:
    name: str
    serial: str
    wwn: str
    size: str
    tran: str
    path: str


@dataclass(frozen=True)
class Bay:
    id: int
    serial: str


@dataclass(frozen=True)
class Snapshot:
    bay: int | None
    z: str
    power: bool


@dataclass(frozen=True)
class LibraryConfig:
    path_contains: str
    bays: tuple[Bay, ...]
