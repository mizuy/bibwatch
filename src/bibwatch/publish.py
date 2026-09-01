"""Publish feeds to docs/feeds/{token}/ for GitHub Pages."""

from __future__ import annotations

from pathlib import Path

from bibwatch.paths import feed_publish_dir


def publish_feed(root: Path, xml: str, *, filename: str = "all.xml") -> Path:
    out_dir = feed_publish_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    path.write_text(xml, encoding="utf-8")
    return path
