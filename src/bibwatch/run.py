"""Orchestrate poll → ingest → RSS publish."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bibwatch.enrich import enrich_paper
from bibwatch.models import Paper
from bibwatch.paths import feed_token
from bibwatch.poll import poll_watch_feeds
from bibwatch.publish import publish_feed
from bibwatch.rss import build_rss, write_feed
from bibwatch.store import load_seen, list_papers, mark_seen, save_paper
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
            if paper.id in seen:
                continue
            existing = None
            from bibwatch.store import load_paper

            existing = load_paper(root, paper.id)
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


def build_feed(root: Path, *, max_items: int = 200, site_base: str | None = None) -> str:
    papers = list_papers(root, limit=max_items)
    token = feed_token(root)
    if site_base:
        feed_link = f"{site_base.rstrip('/')}/feeds/{token}/all.xml"
    else:
        feed_link = f"https://example.github.io/bibwatch/feeds/{token}/all.xml"
    return build_rss(
        papers,
        feed_title="Bibwatch Feed",
        feed_link=feed_link,
        feed_description="Research literature watch feed",
    )


def run_all(
    root: Path,
    *,
    watch_id: str | None = None,
    dry_run: bool = False,
    max_items: int = 200,
    site_base: str | None = None,
) -> RunResult:
    errors: list[str] = []
    new_papers, poll_errors = poll_new_papers(root, watch_id=watch_id, dry_run=dry_run)
    errors.extend(poll_errors)

    if new_papers:
        ingest_papers(root, new_papers, dry_run=dry_run)

    feed_path = None
    if not dry_run:
        xml = build_feed(root, max_items=max_items, site_base=site_base)
        feed_path = publish_feed(root, xml)

    total = len(list_papers(root, limit=max_items))
    return RunResult(new_count=len(new_papers), total_in_feed=total, feed_path=feed_path, errors=errors)
