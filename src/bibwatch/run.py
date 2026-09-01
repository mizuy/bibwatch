"""Orchestrate poll → ingest → RSS publish."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bibwatch.enrich import enrich_paper
from bibwatch.journals import filter_listed_papers, load_journal_catalog, prioritize_papers
from bibwatch.models import Paper
from bibwatch.paths import feed_token, resolve_feed_root
from bibwatch.poll import poll_watch_feeds
from bibwatch.publish import publish_feed
from bibwatch.rss import build_rss, write_feed
from bibwatch.store import load_paper, load_seen, list_papers, mark_seen, save_paper
from bibwatch.translate import translate_paper_abstract
from bibwatch.watch import load_watches


@dataclass
class RunResult:
    new_count: int
    total_in_feed: int
    feed_path: Path | None
    errors: list[str]


def _merge_watch_ids(existing: Paper | None, incoming: Paper) -> list[str]:
    ids = set(incoming.watch_ids)
    if existing:
        ids.update(existing.watch_ids)
    return sorted(ids)


def poll_new_papers(root: Path, *, watch_id: str | None = None, dry_run: bool = False) -> tuple[list[Paper], list[str]]:
    seen = load_seen(root)
    new_papers: list[Paper] = []
    errors: list[str] = []

    for watch in load_watches(root, watch_id=watch_id):
        try:
            fetched = poll_watch_feeds(watch.id, watch.feeds)
        except Exception as e:
            errors.append(f"{watch.id}: {e}")
            continue
        for paper in fetched:
            existing = load_paper(root, paper.id)
            if paper.id in seen:
                if existing:
                    merged = _merge_watch_ids(existing, paper)
                    if merged != existing.watch_ids and not dry_run:
                        existing.watch_ids = merged
                        save_paper(root, existing)
                continue
            paper.watch_ids = _merge_watch_ids(existing, paper)
            if not dry_run:
                seen.add(paper.id)
            new_papers.append(paper)

    return new_papers, errors


def ingest_papers(root: Path, papers: list[Paper], *, dry_run: bool = False) -> list[Paper]:
    ingested: list[Paper] = []
    for paper in papers:
        paper = enrich_paper(paper)
        paper = translate_paper_abstract(root, paper)
        if not dry_run:
            save_paper(root, paper)
            mark_seen(root, paper)
        ingested.append(paper)
    return ingested


def active_watch_ids(root: Path) -> set[str]:
    return {w.id for w in load_watches(root)}


def theme_papers(root: Path) -> list[Paper]:
    active = active_watch_ids(root)
    papers = list_papers(root)
    if not active:
        return papers
    return [p for p in papers if set(p.watch_ids) & active]


def all_feed_papers(root: Path, *, max_items: int = 200) -> list[Paper]:
    catalog = load_journal_catalog(root)
    return prioritize_papers(theme_papers(root), catalog)[:max_items]


def priority_feed_papers(root: Path, *, max_items: int = 200) -> list[Paper]:
    catalog = load_journal_catalog(root)
    papers = filter_listed_papers(theme_papers(root), catalog)
    return prioritize_papers(papers, catalog)[:max_items]


def _feed_link(site_base: str | None, token: str, filename: str) -> str:
    if site_base:
        return f"{site_base.rstrip('/')}/feeds/{token}/{filename}"
    return f"https://example.github.io/bibwatch-feed/feeds/{token}/{filename}"


def build_feed(
    root: Path,
    *,
    max_items: int = 200,
    site_base: str | None = None,
    filename: str = "all.xml",
    priority_only: bool = False,
) -> str:
    papers = (
        priority_feed_papers(root, max_items=max_items)
        if priority_only
        else all_feed_papers(root, max_items=max_items)
    )
    catalog = load_journal_catalog(root)
    token = feed_token(root)
    title = "Bibwatch Priority Feed" if priority_only else "Bibwatch Feed"
    desc = (
        "Listed journals first, then other matches"
        if not priority_only
        else "Papers in the priority journal list"
    )
    return build_rss(
        papers,
        feed_title=title,
        feed_link=_feed_link(site_base, token, filename),
        feed_description=desc,
        journal_catalog=catalog,
    )


def run_all(
    root: Path,
    *,
    watch_id: str | None = None,
    dry_run: bool = False,
    max_items: int = 200,
    site_base: str | None = None,
    feed_root: Path | None = None,
) -> RunResult:
    errors: list[str] = []
    new_papers, poll_errors = poll_new_papers(root, watch_id=watch_id, dry_run=dry_run)
    errors.extend(poll_errors)

    if new_papers:
        ingest_papers(root, new_papers, dry_run=dry_run)

    feed_path = None
    dest = resolve_feed_root(feed_root)
    if not dry_run:
        all_xml = build_feed(root, max_items=max_items, site_base=site_base, filename="all.xml")
        feed_path = publish_feed(root, all_xml, filename="all.xml", feed_root=dest)
        pri_xml = build_feed(
            root,
            max_items=max_items,
            site_base=site_base,
            filename="priority.xml",
            priority_only=True,
        )
        publish_feed(root, pri_xml, filename="priority.xml", feed_root=dest)

    total = len(all_feed_papers(root, max_items=max_items))
    return RunResult(new_count=len(new_papers), total_in_feed=total, feed_path=feed_path, errors=errors)
