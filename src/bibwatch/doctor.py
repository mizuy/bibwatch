"""Health checks for bibwatch-data."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from bibwatch.feeds import load_feeds
from bibwatch.journals import load_journal_catalog, resolve_journals_path
from bibwatch.paths import (
    feed_publish_dir,
    feed_token,
    feeds_path,
    journals_path,
    public_feed_dir,
    resolve_feed_root,
    watches_dir,
)
from bibwatch.watch import list_watch_files


def _check_rss(path: Path, issues: list[str], *, required: bool) -> None:
    if path.is_file():
        try:
            ET.parse(path)
        except ET.ParseError as e:
            issues.append(f"invalid RSS XML ({path.name}): {e}")
    elif required:
        issues.append(f"feed not found: {path} (run `bibwatch run` first)")


def _check_catalog(root: Path, path: Path, issues: list[str]) -> None:
    if not path.is_file():
        issues.append(f"journals file not found: {path}")
        return
    try:
        catalog = load_journal_catalog(root, path=path) or []
        if not catalog:
            issues.append(f"{path.name} has no journals")
    except Exception as e:
        issues.append(f"invalid {path.name}: {e}")


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
        return issues

    try:
        specs = load_feeds(root)
    except Exception as e:
        issues.append(f"invalid feeds.yaml: {e}")
        specs = []

    catalog_paths: set[Path] = set()
    if journals_path(root).is_file():
        catalog_paths.add(journals_path(root))
    explicit_feeds = feeds_path(root).is_file()
    for spec in specs:
        if spec.journals:
            catalog_path = resolve_journals_path(root, spec.journals)
            if catalog_path.is_file() or explicit_feeds:
                catalog_paths.add(catalog_path)
    for catalog_path in sorted(catalog_paths):
        _check_catalog(root, catalog_path, issues)

    try:
        pub_dir = feed_publish_dir(root)
        if not specs:
            _check_rss(pub_dir / "all.xml", issues, required=True)
        for spec in specs:
            required = spec.id == "all" or spec.filename == "all.xml"
            _check_rss(pub_dir / spec.filename, issues, required=required)
    except FileNotFoundError as e:
        issues.append(str(e))

    dest = resolve_feed_root(feed_root)
    if dest is not None:
        try:
            public_dir = public_feed_dir(dest, root)
            if not specs:
                _check_rss(public_dir / "all.xml", issues, required=True)
            for spec in specs:
                required = spec.id == "all" or spec.filename == "all.xml"
                if required:
                    _check_rss(public_dir / spec.filename, issues, required=True)
                elif (public_dir / spec.filename).is_file():
                    _check_rss(public_dir / spec.filename, issues, required=False)
        except FileNotFoundError as e:
            issues.append(str(e))

    if feeds_path(root).is_file() and not specs:
        issues.append("feeds.yaml produced no feeds")

    return issues
