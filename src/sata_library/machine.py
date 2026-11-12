from collections.abc import Callable

from sata_library.errors import LibraryError
from sata_library.model import Disk, LibraryConfig
from sata_library.transport import Transport


class Copier:
    def copy(self, source: str, disk: Disk) -> None:
        raise NotImplementedError


class RecordingCopier(Copier):
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def copy(self, source: str, disk: Disk) -> None:
        self.calls.append((source, disk.serial))
        if self.fail:
            raise LibraryError("copy_failed", "копирование не удалось")


DiskSource = Callable[[], list[Disk]]


class Library:
    def __init__(self, transport: Transport, config: LibraryConfig, disks: DiskSource, copier: Copier) -> None:
        self.transport = transport
        self.config = config
        self.disks = disks
        self.copier = copier
        self._bays = {bay.id: bay for bay in config.bays}

    def identify(self, bay_id: int) -> Disk:
        return self._with_disk(bay_id, lambda disk: disk)

    def backup(self, bay_id: int, source: str) -> Disk:
        bay = self._require_bay(bay_id)
        if bay.serial == "":
            raise LibraryError(
                "unknown_disk",
                "в манифесте нет серийника, сначала identify и запись в конфиг",
            )
        expected = bay.serial

        def action(disk: Disk) -> Disk:
            if disk.serial != expected:
                raise LibraryError(
                    "serial_mismatch",
                    f"в отсеке {disk.serial}, в манифесте {expected}",
                )
            self.copier.copy(source, disk)
            return disk

        return self._with_disk(bay_id, action)

    def _with_disk(self, bay_id: int, action: Callable[[Disk], Disk]) -> Disk:
        self._require_bay(bay_id)
        self._align(bay_id)
        try:
            self.transport.mate()
            self.transport.set_power(True)
            return action(self._one_disk())
        finally:
            self._shutdown()

    def _align(self, bay_id: int) -> None:
        snap = self.transport.state()
        if snap.power or snap.z != "retracted":
            raise LibraryError(
                "not_parked",
                "перед переездом разъём должен быть отведён, питание выключено",
            )
        if snap.bay != bay_id:
            self.transport.seek(bay_id)

    def _one_disk(self) -> Disk:
        needle = self.config.path_contains
        found = [disk for disk in self.disks() if needle == "" or needle in disk.path or needle in disk.name]
        if len(found) != 1:
            raise LibraryError("disk_count", f"на порту библиотеки дисков {len(found)}, нужен один")
        disk = found[0]
        if disk.serial == "":
            raise LibraryError("no_serial", "у диска пустой серийник, такой в манифест не пишем")
        return disk

    def _shutdown(self) -> None:
        if self.transport.state().power:
            self.transport.set_power(False)
        if self.transport.state().z != "retracted":
            try:
                self.transport.retract()
            except LibraryError:
                self.transport.estop()
                raise

    def _require_bay(self, bay_id: int):
        try:
            return self._bays[bay_id]
        except KeyError as exc:
            raise LibraryError("bad_bay", f"отсека {bay_id} нет в манифесте") from exc
