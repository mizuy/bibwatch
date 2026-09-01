"""Publish feeds to docs/feeds/{token}/ and optionally a public Pages checkout."""

from __future__ import annotations

from pathlib import Path

from bibwatch.paths import feed_publish_dir, pages_feed_dir


def publish_feed(
    root: Path,
    xml: str,
    *,
    filename: str = "all.xml",
    pages_root: Path | None = None,
) -> Path:
    out_dir = feed_publish_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    path.write_text(xml, encoding="utf-8")

    if pages_root is not None:
        public_dir = pages_feed_dir(pages_root, root)
        public_dir.mkdir(parents=True, exist_ok=True)
        (public_dir / filename).write_text(xml, encoding="utf-8")

    return path
