"""Health checks for bibwatch-data."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from bibwatch.paths import feed_publish_dir, feed_token, watches_dir
from bibwatch.watch import list_watch_files


def run_doctor(root: Path) -> list[str]:
    issues: list[str] = []

    if not watches_dir(root).is_dir():
        issues.append("missing watches/ directory")
    elif not list_watch_files(root):
        issues.append("no watch definitions in watches/")

    try:
        token = feed_token(root)
        if len(token) < 16:
            issues.append("feed token looks too short")
    except FileNotFoundError as e:
        issues.append(str(e))

    try:
        feed_path = feed_publish_dir(root) / "all.xml"
        if feed_path.is_file():
            ET.parse(feed_path)
        else:
            issues.append(f"feed not found: {feed_path} (run `bibwatch run` first)")
    except ET.ParseError as e:
        issues.append(f"invalid RSS XML: {e}")
    except FileNotFoundError as e:
        issues.append(str(e))

    return issues
