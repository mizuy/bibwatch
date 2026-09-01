"""Health checks for bibwatch-data."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from bibwatch.journals import load_journal_catalog
from bibwatch.paths import (
    feed_publish_dir,
    feed_token,
    journals_path,
    public_feed_dir,
    resolve_feed_root,
    watches_dir,
)
from bibwatch.watch import list_watch_files


def run_doctor(root: Path, *, feed_root: Path | None = None) -> list[str]:
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

    if journals_path(root).is_file():
        try:
            catalog = load_journal_catalog(root) or []
            if not catalog:
                issues.append("journals.yaml has no journals")
        except Exception as e:
            issues.append(f"invalid journals.yaml: {e}")

    dest = resolve_feed_root(feed_root)
    if dest is not None:
        try:
            public_path = public_feed_dir(dest, root) / "all.xml"
            if public_path.is_file():
                ET.parse(public_path)
            else:
                issues.append(
                    f"public feed not found: {public_path} (set BIBWATCH_FEED and run `bibwatch run`)"
                )
            pri_path = public_feed_dir(dest, root) / "priority.xml"
            if pri_path.is_file():
                ET.parse(pri_path)
        except ET.ParseError as e:
            issues.append(f"invalid public RSS XML: {e}")
        except FileNotFoundError as e:
            issues.append(str(e))

    return issues
