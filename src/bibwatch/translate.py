"""Apply Japanese abstract translations (written by the agent, not DeepL)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from bibwatch.feeds import load_feeds
from bibwatch.models import Paper
from bibwatch.paths import translations_dir
from bibwatch.store import load_paper, list_papers, save_paper


def _cache_path(root: Path, paper_id: str) -> Path:
    safe = paper_id.replace(":", "_").replace("/", "_")
    return translations_dir(root) / f"{safe}.yaml"


def load_translation_cache(root: Path, paper_id: str) -> dict | None:
    path = _cache_path(root, paper_id)
    if not path.is_file():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def save_translation_cache(root: Path, paper_id: str, data: dict) -> None:
    path = _cache_path(root, paper_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def translate_paper_abstract(root: Path, paper: Paper, *, target: str = "ja", provider: str = "agent") -> Paper:
    """Attach a cached Japanese abstract if one exists. Does not call an API."""
    if paper.abstract.ja:
        paper.abstract.translated = True
        return paper
    if not paper.abstract.original:
        return paper
    cached = load_translation_cache(root, paper.id)
    if cached and cached.get("abstract_ja"):
        paper.abstract.ja = cached["abstract_ja"]
        paper.abstract.translated = True
    return paper


def needs_translation(paper: Paper) -> bool:
    return bool(paper.abstract.original) and not bool(paper.abstract.ja)


def feed_paper_ids(root: Path) -> set[str]:
    from bibwatch.run import papers_for_feed

    ids: set[str] = set()
    for spec in load_feeds(root):
        for paper in papers_for_feed(root, spec):
            ids.add(paper.id)
    return ids


def papers_needing_translation(root: Path, *, in_feeds: bool = True) -> list[Paper]:
    papers = [p for p in list_papers(root) if needs_translation(p)]
    if in_feeds:
        wanted = feed_paper_ids(root)
        papers = [p for p in papers if p.id in wanted]
    return papers


def apply_abstract_translation(root: Path, paper_id: str, ja: str, *, provider: str = "agent") -> Paper:
    paper = load_paper(root, paper_id)
    if paper is None:
        raise FileNotFoundError(f"paper not found: {paper_id}")
    text = (ja or "").strip()
    if not text:
        raise ValueError(f"{paper_id}: empty translation")
    paper.abstract.ja = text
    paper.abstract.translated = True
    save_translation_cache(
        root,
        paper.id,
        {
            "paper_id": paper.id,
            "abstract_original": paper.abstract.original,
            "abstract_ja": text,
            "provider": provider,
        },
    )
    save_paper(root, paper)
    return paper


def apply_translations_file(root: Path, path: Path, *, provider: str = "agent") -> list[str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(raw, dict):
        rows = raw.get("translations") or raw.get("papers") or []
    elif isinstance(raw, list):
        rows = raw
    else:
        raise ValueError(f"Invalid translations file: {path}")
    applied: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            paper_id = str(row.get("id") or row.get("paper_id") or "").strip()
            ja = str(row.get("ja") or row.get("abstract_ja") or "")
        else:
            continue
        if not paper_id:
            continue
        apply_abstract_translation(root, paper_id, ja, provider=provider)
        applied.append(paper_id)
    return applied


def pending_payload(paper: Paper) -> dict[str, Any]:
    return {
        "id": paper.id,
        "title": paper.title,
        "journal": paper.journal.name or paper.journal.iso_abbrev,
        "abstract": paper.abstract.original,
    }
