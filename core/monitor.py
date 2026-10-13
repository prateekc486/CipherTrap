"""
Folder monitoring module for CipherTrap.

Watches a directory tree and publishes normalized filesystem events.
Two independent outputs are provided:

1. Debounced `FileEvent` objects (for UI / audit log display).
2. Raw `RawEventStats` counters per path (for the risk engine), which are
   NEVER debounced -- every single filesystem event increments them, even
   if it happens 50 times a second on the same file. This is critical
   because rapid repeated writes to one file is a strong ransomware signal
   that debouncing would otherwise hide.

This module does not calculate risk, inspect honeyfiles, create snapshots,
or modify files. Those responsibilities belong to separate modules.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Literal

from watchdog.events import (
    DirMovedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

EventType = Literal["created", "modified", "deleted", "moved"]
EventCallback = Callable[["FileEvent"], None]


@dataclass(frozen=True, slots=True)
class FileEvent:
    """Normalized, debounced filesystem event for UI/audit consumption."""

    event_type: EventType
    path: Path
    is_directory: bool
    timestamp: float
    source_path: Path | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "event_type": self.event_type,
            "path": str(self.path),
            "is_directory": self.is_directory,
            "timestamp": self.timestamp,
            "source_path": str(self.source_path) if self.source_path else None,
        }


@dataclass(slots=True)
class RawEventStats:
    """
    Un-debounced activity counters for a single file path.

    The risk engine should read these directly rather than counting
    delivered FileEvent objects, since delivered events are throttled
    for display purposes and will under-count rapid activity.
    """

    path: Path
    event_count: int = 0          # total raw events ever seen for this path
    suppressed_count: int = 0     # events that were debounced (not delivered)
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    def as_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "event_count": self.event_count,
            "suppressed_count": self.suppressed_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


class _WatchdogHandler(FileSystemEventHandler):
    """Translates watchdog events into FolderMonitor calls."""

    def __init__(self, monitor: "FolderMonitor") -> None:
        super().__init__()
        self._monitor = monitor

    def on_created(self, event: FileSystemEvent) -> None:
        self._monitor._publish_event(
            event_type="created", path=Path(event.src_path), is_directory=event.is_directory,
        )

    def on_modified(self, event: FileSystemEvent) -> None:
        self._monitor._publish_event(
            event_type="modified", path=Path(event.src_path), is_directory=event.is_directory,
        )

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._monitor._publish_event(
            event_type="deleted", path=Path(event.src_path), is_directory=event.is_directory,
        )

    def on_moved(self, event: FileSystemEvent) -> None:
        if not isinstance(event, (FileMovedEvent, DirMovedEvent)):
            return
        self._monitor._publish_event(
            event_type="moved",
            path=Path(event.dest_path),
            source_path=Path(event.src_path),
            is_directory=event.is_directory,
        )


class FolderMonitor:
    """Watch a folder and publish normalized filesystem events."""

    def __init__(
        self,
        root_path: str | Path,
        *,
        callback: EventCallback | None = None,
        raw_stats_callback: Callable[[RawEventStats, EventType], None] | None = None,
        event_queue: "queue.Queue[FileEvent]" | None = None,
        recursive: bool = True,
        ignored_paths: Iterable[str | Path] = (),
        debounce_seconds: float = 0.25,
    ) -> None:
        root = Path(root_path).expanduser().resolve(strict=False)

        if not root.exists():
            raise FileNotFoundError(f"Monitored folder does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Monitored path is not a directory: {root}")
        if debounce_seconds < 0:
            raise ValueError("debounce_seconds must be non-negative")

        self.root_path = root
        self.callback = callback
        self.raw_stats_callback = raw_stats_callback
        self.event_queue = event_queue or queue.Queue()
        self.recursive = recursive
        self.debounce_seconds = debounce_seconds

        self._ignored_paths = tuple(
            Path(p).expanduser().resolve(strict=False) for p in ignored_paths
        )

        self._observer: Observer | None = None
        self._lock = threading.RLock()
        self._last_event_times: dict[tuple[str, str, str], float] = {}

        # raw, never-debounced per-path stats -- this is what the risk
        # engine should read for true activity volume
        self._raw_stats: dict[str, RawEventStats] = {}

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._observer is not None and self._observer.is_alive()

    def start(self) -> None:
        with self._lock:
            if self.is_running:
                return
            observer = Observer()
            observer.schedule(_WatchdogHandler(self), str(self.root_path), recursive=self.recursive)
            observer.start()
            self._observer = observer
        logger.info("Started folder monitoring: root=%s recursive=%s", self.root_path, self.recursive)

    def stop(self) -> None:
        with self._lock:
            observer = self._observer
            if observer is None:
                return
            observer.stop()
            self._observer = None
        logger.info("Stopped folder monitoring: root=%s", self.root_path)

    def join(self, timeout: float | None = None) -> None:
        with self._lock:
            observer = self._observer
        if observer is not None:
            observer.join(timeout=timeout)

    def get_event(self, timeout: float | None = None) -> FileEvent:
        return self.event_queue.get(timeout=timeout)

    def get_raw_stats(self, path: str | Path) -> RawEventStats | None:
        """Return the raw (un-debounced) stats for a given path, if any."""
        with self._lock:
            return self._raw_stats.get(str(Path(path).expanduser().resolve(strict=False)))

    def all_raw_stats(self) -> list[RawEventStats]:
        """Return raw stats for every path seen so far."""
        with self._lock:
            return list(self._raw_stats.values())

    def reset_raw_stats(self) -> None:
        """Clear raw stats (e.g. after the risk engine has scored a window)."""
        with self._lock:
            self._raw_stats.clear()

    def __enter__(self) -> "FolderMonitor":
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()
        self.join()

    def _publish_event(
        self, *, event_type: EventType, path: Path, is_directory: bool, source_path: Path | None = None,
    ) -> None:
        normalized_path = path.expanduser().resolve(strict=False)
        normalized_source_path = (
            source_path.expanduser().resolve(strict=False) if source_path is not None else None
        )

        if self._is_ignored(normalized_path):
            return
        if normalized_source_path is not None and self._is_ignored(normalized_source_path):
            return

        now = time.monotonic()

        # --- RAW STATS: always updated, never debounced, never skipped ---
        # This is the fix: ransomware doing 50 rapid writes to one file must
        # show up as 50 in raw stats even though only 1-2 FileEvents get
        # delivered downstream.
        with self._lock:
            key = str(normalized_path)
            stats = self._raw_stats.get(key)
            if stats is None:
                stats = RawEventStats(path=normalized_path)
                self._raw_stats[key] = stats
            stats.event_count += 1
            stats.last_seen = time.time()

        if self.raw_stats_callback is not None:
            try:
                self.raw_stats_callback(stats, event_type)
            except Exception:
                logger.exception("raw_stats_callback failed for path=%s", normalized_path)

        # --- DEBOUNCED DELIVERY: for UI / audit log, not for scoring ---
        dedupe_key = (event_type, str(normalized_path), str(normalized_source_path or ""))
        if self._is_debounced(dedupe_key, now):
            with self._lock:
                stats.suppressed_count += 1
            return

        file_event = FileEvent(
            event_type=event_type,
            path=normalized_path,
            source_path=normalized_source_path,
            is_directory=is_directory,
            timestamp=time.time(),
        )
        self.event_queue.put(file_event)

        if self.callback is not None:
            try:
                self.callback(file_event)
            except Exception:
                logger.exception("Filesystem event callback failed: event=%s path=%s", event_type, normalized_path)

    def _is_ignored(self, path: Path) -> bool:
        for ignored_path in self._ignored_paths:
            if path == ignored_path:
                return True
            try:
                path.relative_to(ignored_path)
            except ValueError:
                continue
            else:
                return True
        return False

    def _is_debounced(self, event_key: tuple[str, str, str], now: float) -> bool:
        if self.debounce_seconds == 0:
            return False
        with self._lock:
            previous_time = self._last_event_times.get(event_key)
            self._last_event_times[event_key] = now
            if previous_time is None:
                return False
            return now - previous_time < self.debounce_seconds
