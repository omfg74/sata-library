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
class DiskEntry:
    slot: int
    index: int
    serial: str
    path_contains: str
    mount: str


@dataclass(frozen=True)
class ShelfState:
    slots: tuple[bool, bool, bool, bool]
    present: tuple[bool, bool, bool, bool]
    disks: tuple[bool, bool, bool, bool]


@dataclass(frozen=True)
class LibraryConfig:
    spin_pause_s: float
    disks: tuple[DiskEntry, ...]
