"""Named RSS feeds from feeds.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from bibwatch.paths import feeds_path


@dataclass(frozen=True)
class FeedSpec:
    id: str
    filename: str
    title: str
    description: str = ""
    watches: tuple[str, ...] | None = None
    journals: str | None = None
    prioritize: bool = True
    listed_only: bool = False
    max_items: int = 200


DEFAULT_FEEDS: tuple[FeedSpec, ...] = (
    FeedSpec(
        id="all",
        filename="all.xml",
        title="Bibwatch Feed",
        description="Listed journals first, then other matches",
        journals="journals.yaml",
        prioritize=True,
        listed_only=False,
    ),
    FeedSpec(
        id="priority",
        filename="priority.xml",
        title="Bibwatch Priority Feed",
        description="Papers in the priority journal list",
        journals="journals.yaml",
        prioritize=True,
        listed_only=True,
    ),
)


def _from_dict(data: dict[str, Any]) -> FeedSpec:
    fid = str(data.get("id") or "").strip()
    if not fid:
        raise ValueError("feed entry missing id")
    filename = str(data.get("filename") or f"{fid}.xml").strip()
    if filename != Path(filename).name or "/" in filename or "\\" in filename:
        raise ValueError(f"invalid feed filename: {filename}")
    if not filename.endswith(".xml"):
        raise ValueError(f"feed filename must end with .xml: {filename}")
    watches = data.get("watches")
    watch_ids: tuple[str, ...] | None
    if watches is None:
        watch_ids = None
    elif isinstance(watches, str):
        watch_ids = (watches.strip(),) if watches.strip() else None
    else:
        watch_ids = tuple(str(w).strip() for w in watches if str(w).strip())
    journals = data.get("journals")
    journals_rel: str | None
    if journals is False or journals is None:
        journals_rel = None
    else:
        journals_rel = str(journals).strip() or None
    title = str(data.get("title") or fid).strip()
    description = str(data.get("description") or "").strip()
    max_items = int(data.get("max_items") or 200)
    if max_items < 1:
        raise ValueError(f"{fid}: max_items must be >= 1")
    return FeedSpec(
        id=fid,
        filename=filename,
        title=title,
        description=description,
        watches=watch_ids,
        journals=journals_rel,
        prioritize=bool(data.get("prioritize", True)),
        listed_only=bool(data.get("listed_only", False)),
        max_items=max_items,
    )


def load_feeds(root: Path) -> list[FeedSpec]:
    path = feeds_path(root)
    if not path.is_file():
        return list(DEFAULT_FEEDS)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict):
        rows = raw.get("feeds") or []
    else:
        raise ValueError(f"Invalid feeds file: {path}")
    if not rows:
        return list(DEFAULT_FEEDS)
    return [_from_dict(row) for row in rows]
