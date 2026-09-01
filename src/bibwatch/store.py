"""Paper identity, deduplication, and persistence."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from bibwatch.models import Paper
from bibwatch.paths import papers_dir, seen_path


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    doi = value.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi or None


def paper_id_from_ids(
    *,
    doi: str | None = None,
    pmid: str | None = None,
    arxiv: str | None = None,
    title: str | None = None,
) -> str:
    if doi := normalize_doi(doi):
        return f"doi:{doi}"
    if pmid:
        return f"pmid:{pmid.strip()}"
    if arxiv:
        arx = arxiv.strip().lower().replace("arxiv:", "")
        return f"arxiv:{arx}"
    digest = hashlib.sha256((title or "untitled").encode()).hexdigest()[:16]
    return f"hash:{digest}"


def load_seen(root: Path) -> set[str]:
    path = seen_path(root)
    if not path.is_file():
        return set()
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            seen.add(json.loads(line)["id"])
        except (json.JSONDecodeError, KeyError):
            continue
    return seen


def mark_seen(root: Path, paper: Paper) -> None:
    path = seen_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"id": paper.id, "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def paper_storage_path(root: Path, paper_id: str) -> Path:
    safe = paper_id.replace(":", "_").replace("/", "_")
    return papers_dir(root) / f"{safe}.yaml"


def save_paper(root: Path, paper: Paper) -> Path:
    path = paper_storage_path(root, paper.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(paper.to_dict(), allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def load_paper(root: Path, paper_id: str) -> Paper | None:
    path = paper_storage_path(root, paper_id)
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Paper.from_dict(data)


def list_papers(root: Path, *, limit: int | None = None) -> list[Paper]:
    pdir = papers_dir(root)
    if not pdir.is_dir():
        return []
    paths = sorted(pdir.glob("*.yaml"), key=lambda p: p.stat().st_mtime, reverse=True)
    papers: list[Paper] = []
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        papers.append(Paper.from_dict(data))
        if limit and len(papers) >= limit:
            break
    return papers
