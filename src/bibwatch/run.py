"""Orchestrate poll → ingest → RSS publish."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from bibwatch.enrich import enrich_paper
from bibwatch.feeds import DEFAULT_FEEDS, FeedSpec, load_feeds
from bibwatch.journals import ListedJournal, filter_listed_papers, load_journal_catalog, prioritize_papers
from bibwatch.models import Paper
from bibwatch.paths import feed_token, resolve_feed_root
from bibwatch.poll import poll_watch_feeds
from bibwatch.publish import publish_feed
from bibwatch.rss import build_rss
from bibwatch.store import load_paper, load_seen, list_papers, mark_seen, save_paper
from bibwatch.translate import translate_paper_abstract
from bibwatch.watch import load_watches


@dataclass
class RunResult:
    new_count: int
    total_in_feed: int
    feed_path: Path | None
    errors: list[str]
    feed_paths: list[Path] = field(default_factory=list)


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


def papers_matching_watches(root: Path, watch_ids: tuple[str, ...] | None) -> list[Paper]:
    if watch_ids is None:
        return theme_papers(root)
    wanted = set(watch_ids)
    return [p for p in list_papers(root) if set(p.watch_ids) & wanted]


def catalog_for_feed(root: Path, spec: FeedSpec) -> list[ListedJournal] | None:
    if spec.journals is None:
        return None
    return load_journal_catalog(root, path=spec.journals)


def papers_for_feed(root: Path, spec: FeedSpec, *, max_items: int | None = None) -> list[Paper]:
    papers = papers_matching_watches(root, spec.watches)
    catalog = catalog_for_feed(root, spec)
    if spec.listed_only:
        papers = filter_listed_papers(papers, catalog)
    if spec.prioritize:
        papers = prioritize_papers(papers, catalog)
    else:
        papers = prioritize_papers(papers, None)
    limit = spec.max_items if max_items is None else max_items
    return papers[:limit]


def all_feed_papers(root: Path, *, max_items: int = 200) -> list[Paper]:
    specs = {s.id: s for s in load_feeds(root)}
    spec = specs.get("all") or DEFAULT_FEEDS[0]
    return papers_for_feed(root, spec, max_items=max_items)


def priority_feed_papers(root: Path, *, max_items: int = 200) -> list[Paper]:
    specs = {s.id: s for s in load_feeds(root)}
    spec = specs.get("priority") or DEFAULT_FEEDS[1]
    return papers_for_feed(root, spec, max_items=max_items)


def _feed_link(site_base: str | None, token: str, filename: str) -> str:
    if site_base:
        return f"{site_base.rstrip('/')}/feeds/{token}/{filename}"
    return f"https://example.github.io/bibwatch-feed/feeds/{token}/{filename}"


def build_named_feed(
    root: Path,
    spec: FeedSpec,
    *,
    site_base: str | None = None,
    max_items: int | None = None,
) -> str:
    papers = papers_for_feed(root, spec, max_items=max_items)
    catalog = catalog_for_feed(root, spec)
    token = feed_token(root)
    return build_rss(
        papers,
        feed_title=spec.title,
        feed_link=_feed_link(site_base, token, spec.filename),
        feed_description=spec.description,
        journal_catalog=catalog,
    )


def build_feed(
    root: Path,
    *,
    max_items: int = 200,
    site_base: str | None = None,
    filename: str = "all.xml",
    priority_only: bool = False,
) -> str:
    specs = {s.id: s for s in load_feeds(root)}
    if priority_only:
        spec = specs.get("priority") or DEFAULT_FEEDS[1]
    else:
        spec = specs.get("all") or DEFAULT_FEEDS[0]
    if filename != spec.filename:
        spec = replace(spec, filename=filename)
    return build_named_feed(root, spec, site_base=site_base, max_items=max_items)


def run_all(
    root: Path,
    *,
    watch_id: str | None = None,
    dry_run: bool = False,
    max_items: int | None = None,
    site_base: str | None = None,
    feed_root: Path | None = None,
) -> RunResult:
    errors: list[str] = []
    new_papers, poll_errors = poll_new_papers(root, watch_id=watch_id, dry_run=dry_run)
    errors.extend(poll_errors)

    if new_papers:
        ingest_papers(root, new_papers, dry_run=dry_run)

    feed_path = None
    feed_paths: list[Path] = []
    dest = resolve_feed_root(feed_root)
    specs = load_feeds(root)
    if not dry_run:
        for spec in specs:
            xml = build_named_feed(root, spec, site_base=site_base, max_items=max_items)
            path = publish_feed(root, xml, filename=spec.filename, feed_root=dest)
            feed_paths.append(path)
            if feed_path is None:
                feed_path = path

    primary = specs[0] if specs else DEFAULT_FEEDS[0]
    total = len(papers_for_feed(root, primary, max_items=max_items))
    return RunResult(
        new_count=len(new_papers),
        total_in_feed=total,
        feed_path=feed_path,
        errors=errors,
        feed_paths=feed_paths,
    )
