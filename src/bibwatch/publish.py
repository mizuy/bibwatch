"""Publish feeds to docs/feeds/{token}/ and the public bibwatch-feed checkout."""

from __future__ import annotations

from pathlib import Path

from bibwatch.paths import feed_publish_dir, public_feed_dir


def _write_feed_file(out_dir: Path, xml: str, filename: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    path.write_text(xml, encoding="utf-8")
    nojekyll = out_dir.parents[1] / ".nojekyll"  # docs/.nojekyll
    if nojekyll.parent.name == "docs":
        nojekyll.touch()
    return path


def publish_feed(
    root: Path,
    xml: str,
    *,
    filename: str = "all.xml",
    feed_root: Path | None = None,
) -> Path:
    path = _write_feed_file(feed_publish_dir(root), xml, filename)

    if feed_root is not None:
        _write_feed_file(public_feed_dir(feed_root, root), xml, filename)

    return path
