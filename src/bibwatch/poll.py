"""Fetch and parse literature RSS feeds."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from bibwatch.models import Abstract, Journal, Paper
from bibwatch.store import normalize_doi, paper_id_from_ids


def fetch_feed(url: str, *, timeout: float = 30.0) -> feedparser.FeedParserDict:
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        resp = client.get(url, headers={"User-Agent": "bibwatch/0.1"})
        resp.raise_for_status()
    return feedparser.parse(resp.content)


def _first_link(entry: Any) -> str | None:
    if getattr(entry, "link", None):
        return entry.link
    for link in getattr(entry, "links", []) or []:
        if link.get("href"):
            return link["href"]
    return None


def _entry_published(entry: Any) -> str | None:
    for attr in ("published", "updated", "created"):
        if getattr(entry, attr, None):
            return getattr(entry, attr)
    if getattr(entry, "published_parsed", None):
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.date().isoformat()
        except (TypeError, ValueError):
            pass
    return None


def _extract_pmid(link: str | None) -> str | None:
    if not link:
        return None
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", link)
    return m.group(1) if m else None


def _extract_doi_from_text(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"10\.\d{4,9}/[^\s<>\"']+", text)
    return m.group(0).rstrip(".,)") if m else None


def _extract_arxiv(link: str | None, entry_id: str | None) -> str | None:
    for src in (link or "", entry_id or ""):
        m = re.search(r"arxiv\.org/abs/([\d.]+(?:v\d+)?)", src, re.I)
        if m:
            return m.group(1)
    return None


def _parse_pubmed_item(entry: Any, watch_id: str) -> Paper:
    title = (getattr(entry, "title", None) or "").strip()
    summary = (getattr(entry, "summary", None) or getattr(entry, "description", None) or "").strip()
    link = _first_link(entry)
    pmid = _extract_pmid(link) or _extract_pmid(getattr(entry, "id", ""))
    doi = _extract_doi_from_text(summary) or _extract_doi_from_text(title)

    journal_name = None
    m = re.search(r"<strong>Source:</strong>\s*([^<]+)", summary)
    if m:
        journal_name = m.group(1).strip()

    abstract_original = re.sub(r"<[^>]+>", " ", summary)
    abstract_original = re.sub(r"\s+", " ", abstract_original).strip()

    paper_id = paper_id_from_ids(doi=doi, pmid=pmid, title=title)
    ids: dict[str, str] = {}
    if doi:
        ids["doi"] = normalize_doi(doi) or doi
    if pmid:
        ids["pmid"] = pmid

    urls: dict[str, str] = {}
    if link:
        urls["landing"] = link
    if doi:
        norm = normalize_doi(doi)
        if norm:
            urls["doi"] = f"https://doi.org/{norm}"

    return Paper(
        id=paper_id,
        title=title,
        watch_ids=[watch_id],
        journal=Journal(name=journal_name, published=_entry_published(entry), type="journal"),
        abstract=Abstract(original=abstract_original or None),
        urls=urls,
        ids=ids,
        fetched_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )


def _parse_arxiv_item(entry: Any, watch_id: str) -> Paper:
    title = (getattr(entry, "title", None) or "").strip().replace("\n", " ")
    summary = (getattr(entry, "summary", None) or "").strip().replace("\n", " ")
    link = _first_link(entry)
    entry_id = getattr(entry, "id", None)
    arxiv_id = _extract_arxiv(link, entry_id)

    paper_id = paper_id_from_ids(arxiv=arxiv_id, title=title)
    ids = {"arxiv": arxiv_id} if arxiv_id else {}
    urls = {"landing": link} if link else {}
    if arxiv_id:
        urls["pdf"] = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    return Paper(
        id=paper_id,
        title=title,
        watch_ids=[watch_id],
        journal=Journal(name="arXiv", type="preprint", published=_entry_published(entry)),
        abstract=Abstract(original=summary or None),
        urls=urls,
        ids=ids,
        fetched_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )


def parse_feed_entry(entry: Any, watch_id: str, feed: dict[str, str]) -> Paper:
    feed_type = feed.get("type", "generic")
    if feed_type in {"pubmed_rss", "pubmed"}:
        return _parse_pubmed_item(entry, watch_id)
    if feed_type in {"arxiv", "arxiv_rss"}:
        return _parse_arxiv_item(entry, watch_id)
    title = (getattr(entry, "title", None) or "Untitled").strip()
    summary = (getattr(entry, "summary", None) or "").strip()
    link = _first_link(entry)
    doi = _extract_doi_from_text(summary)
    paper_id = paper_id_from_ids(doi=doi, title=title)
    ids: dict[str, str] = {}
    norm = normalize_doi(doi)
    if norm:
        ids["doi"] = norm
    return Paper(
        id=paper_id,
        title=title,
        watch_ids=[watch_id],
        abstract=Abstract(original=summary or None),
        urls={"landing": link} if link else {},
        ids=ids,
        fetched_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )


def poll_watch_feeds(watch_id: str, feeds: list[dict[str, str]]) -> list[Paper]:
    papers: list[Paper] = []
    for feed in feeds:
        url = feed.get("url")
        if not url:
            continue
        parsed = fetch_feed(url)
        for entry in parsed.entries:
            papers.append(parse_feed_entry(entry, watch_id, feed))
    return papers
