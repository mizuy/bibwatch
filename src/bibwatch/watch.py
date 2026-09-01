"""Load watch definitions from bibwatch-data."""

from __future__ import annotations

from pathlib import Path

import yaml

from bibwatch.models import Paper, Watch
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


def load_all_watches(root: Path) -> list[Watch]:
    return [load_watch(path) for path in list_watch_files(root)]


def load_watches(root: Path, *, watch_id: str | None = None) -> list[Watch]:
    watches: list[Watch] = []
    for watch in load_all_watches(root):
        if not watch.enabled:
            continue
        if watch_id and watch.id != watch_id:
            continue
        watches.append(watch)
    return watches


def title_abstract_blob(paper: Paper) -> str:
    return f"{paper.title or ''}\n{paper.abstract.original or ''}".lower()


def matches_require_tiab(paper: Paper, phrases: list[str] | None) -> bool:
    if not phrases:
        return True
    blob = title_abstract_blob(paper)
    return any(phrase.lower() in blob for phrase in phrases if phrase.strip())


def paper_matches_watch(paper: Paper, watch: Watch) -> bool:
    if watch.id not in paper.watch_ids:
        return False
    return matches_require_tiab(paper, watch.require_tiab)
