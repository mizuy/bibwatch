"""Load watch definitions from bibwatch-data."""

from __future__ import annotations

from pathlib import Path

import yaml

from bibwatch.models import Watch
from bibwatch.paths import watches_dir


def list_watch_files(root: Path) -> list[Path]:
    wdir = watches_dir(root)
    if not wdir.is_dir():
        return []
    return sorted(wdir.glob("*.yaml"))


def load_watch(path: Path) -> Watch:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "id" not in data:
        raise ValueError(f"Invalid watch file: {path}")
    return Watch.from_dict(data)


def load_watches(root: Path, *, watch_id: str | None = None) -> list[Watch]:
    watches: list[Watch] = []
    for path in list_watch_files(root):
        watch = load_watch(path)
        if not watch.enabled:
            continue
        if watch_id and watch.id != watch_id:
            continue
        watches.append(watch)
    return watches
