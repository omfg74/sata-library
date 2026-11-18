import subprocess
import time
from collections.abc import Callable

from sata_library.errors import LibraryError
from sata_library.model import Disk, DiskEntry, LibraryConfig
from sata_library.transport import Transport


class Copier:
    def copy(self, source: str, disk: Disk, mount: str) -> None:
        raise NotImplementedError


class RecordingCopier(Copier):
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def copy(self, source: str, disk: Disk, mount: str) -> None:
        self.calls.append((source, disk.serial))
        if self.fail:
            raise LibraryError("copy_failed", "копирование не удалось")


class RsyncCopier(Copier):
    """Архив пишет rsync в уже смонтированный каталог диска. Сухой прогон сюда не заходит."""

    def __init__(self, run: Callable[..., subprocess.CompletedProcess[str]] | None = None) -> None:
        self._run = run or subprocess.run

    def copy(self, source: str, disk: Disk, mount: str) -> None:
        del disk
        if source == "":
            raise LibraryError("no_source", "пустой источник")
        if mount == "":
            raise LibraryError("no_mount", "в манифесте нет каталога mount")
        src = source if source.endswith("/") else source + "/"
        dst = mount if mount.endswith("/") else mount + "/"
        try:
            result = self._run(
                ["rsync", "-a", "--", src, dst],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            raise LibraryError("copy_failed", "rsync не запустился") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise LibraryError("copy_failed", detail or f"rsync завершился с кодом {result.returncode}")


DiskSource = Callable[[], list[Disk]]


class Library:
    def __init__(
        self,
        transport: Transport,
        config: LibraryConfig,
        disks: DiskSource,
        copier: Copier,
        *,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        ready_s: float = 30.0,
        poll_s: float = 0.25,
        dry_run: bool = False,
    ) -> None:
        self.transport = transport
        self.config = config
        self.disks = disks
        self.copier = copier
        self.sleeper = sleeper
        self.clock = clock
        self.ready_s = ready_s
        self.poll_s = poll_s
        self.dry_run = dry_run
        self._entries = {(entry.slot, entry.index): entry for entry in config.disks}
        self._started = False

    def identify(self, slot: int, index: int) -> Disk:
        entry = self._require(slot, index)
        return self._with_disk(entry, lambda disk: disk)

    def backup(self, slot: int, index: int, source: str) -> Disk:
        entry = self._require(slot, index)
        if entry.serial == "":
            raise LibraryError(
                "unknown_disk",
                "в манифесте нет серийника, сначала identify и запись в конфиг",
            )
        expected = entry.serial

        def action(disk: Disk) -> Disk:
            if disk.serial != expected:
                raise LibraryError(
                    "serial_mismatch",
                    f"на диске {disk.serial}, в манифесте {expected}",
                )
            self.copier.copy(source, disk, entry.mount)
            return disk

        return self._with_disk(entry, action)

    def _with_disk(self, entry: DiskEntry, action: Callable[[Disk], Disk]) -> Disk:
        if not self.dry_run and entry.path_contains == "":
            raise LibraryError(
                "path_filter",
                "пустой path_contains: диск компьютера нельзя отличить от полки",
            )
        opened = False
        try:
            self._ensure_slot(entry.slot)
            opened = True
            self._ensure_disk(entry.slot, entry.index)
            return action(self._await_disk(entry))
        finally:
            if opened:
                self._shutdown(entry.slot, entry.index)

    def _ensure_slot(self, slot: int) -> None:
        if self.transport.state().slots[slot - 1]:
            return
        self.transport.slot_on(slot)
        self._started = False

    def _ensure_disk(self, slot: int, index: int) -> None:
        state = self.transport.state()
        if state.disks[index - 1]:
            return
        if self._started or any(state.disks):
            self.sleeper(self.config.spin_pause_s)
        self.transport.disk_on(slot, index)
        self._started = True

    def _await_disk(self, entry: DiskEntry) -> Disk:
        deadline = self.clock() + self.ready_s
        while True:
            found = self._matching(entry)
            if len(found) == 1:
                disk = found[0]
                if disk.serial == "":
                    raise LibraryError("no_serial", "у диска пустой серийник, такой в манифест не пишем")
                return disk
            if len(found) > 1:
                raise LibraryError("disk_count", f"на порту библиотеки дисков {len(found)}, нужен один")
            if self.clock() >= deadline:
                raise LibraryError("disk_count", "на порту библиотеки дисков 0, нужен один")
            self.sleeper(self.poll_s)

    def _matching(self, entry: DiskEntry) -> list[Disk]:
        needle = entry.path_contains
        found = self.disks()
        if needle == "":
            return list(found)
        return [disk for disk in found if needle in disk.path or needle in disk.name]

    def _shutdown(self, slot: int, index: int) -> None:
        try:
            if self.transport.state().disks[index - 1]:
                self.transport.disk_off(slot, index)
            if self.transport.state().slots[slot - 1]:
                self.transport.slot_off(slot)
        except LibraryError:
            self.transport.estop()
            raise

    def _require(self, slot: int, index: int) -> DiskEntry:
        try:
            return self._entries[(slot, index)]
        except KeyError as exc:
            raise LibraryError("bad_disk", f"слота {slot} диска {index} нет в манифесте") from exc
