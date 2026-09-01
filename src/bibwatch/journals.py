"""Priority journal catalog for RSS ordering and labels."""

from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from bibwatch.models import Paper
from bibwatch.paths import journals_path


@dataclass(frozen=True)
class ListedJournal:
    name: str
    abbrev: str | None = None
    if_2025: float | None = None
    if_2025_flag: str = ""
    if_2020: float | None = None
    memo: str | None = None
    aliases: tuple[str, ...] = ()

    def keys(self) -> set[str]:
        out = {normalize_journal_name(self.name)}
        if self.abbrev:
            out.add(normalize_journal_name(self.abbrev))
        for alias in self.aliases:
            out.add(normalize_journal_name(alias))
        return {k for k in out if k}


def normalize_journal_name(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(str(value))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if text.startswith("the "):
        text = text[4:]
    return text


def _parse_if(value: Any) -> tuple[float | None, str]:
    if value is None:
        return None, ""
    if isinstance(value, bool):
        return None, ""
    if isinstance(value, (int, float)):
        return float(value), ""
    text = str(value).strip()
    if text.lower() in {"", "—", "-", "–", "none", "null", "n/a"}:
        return None, ""
    flag = ""
    if text.endswith("*"):
        flag = "*"
        text = text[:-1].strip()
    try:
        return float(text), flag
    except ValueError:
        return None, ""


def _from_dict(data: dict[str, Any]) -> ListedJournal:
    name = str(data.get("name") or "").strip()
    if not name:
        raise ValueError("journal entry missing name")
    if_2025, flag = _parse_if(data.get("if_2025"))
    if_2020, _ = _parse_if(data.get("if_2020"))
    aliases = data.get("aliases") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    return ListedJournal(
        name=name,
        abbrev=(str(data["abbrev"]).strip() if data.get("abbrev") else None),
        if_2025=if_2025,
        if_2025_flag=flag or str(data.get("if_2025_flag") or ""),
        if_2020=if_2020,
        memo=(str(data["memo"]).strip() if data.get("memo") else None),
        aliases=tuple(str(a).strip() for a in aliases if str(a).strip()),
    )


def load_journal_catalog(root: Path) -> list[ListedJournal] | None:
    """Return listed journals, or None if no allowlist file exists."""
    path = journals_path(root)
    if not path.is_file():
        return None
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict):
        rows = raw.get("journals") or []
    else:
        raise ValueError(f"Invalid journals file: {path}")
    return [_from_dict(row) for row in rows]


def match_journal(paper: Paper, catalog: list[ListedJournal] | None) -> ListedJournal | None:
    if not catalog:
        return None
    candidates = {
        normalize_journal_name(paper.journal.name),
        normalize_journal_name(paper.journal.iso_abbrev),
    }
    candidates.discard("")
    if not candidates:
        return None
    for listed in catalog:
        if candidates & listed.keys():
            return listed
    return None


def filter_listed_papers(papers: list[Paper], catalog: list[ListedJournal] | None) -> list[Paper]:
    if catalog is None:
        return papers
    return [p for p in papers if match_journal(p, catalog) is not None]


def _paper_date_key(paper: Paper) -> float:
    raw = paper.journal.published or paper.fetched_at or ""
    try:
        if len(raw) >= 10:
            return datetime.fromisoformat(raw[:10]).timestamp()
        if len(raw) == 4:
            return datetime(int(raw), 1, 1).timestamp()
    except (ValueError, TypeError):
        return 0.0
    return 0.0


def prioritize_papers(papers: list[Paper], catalog: list[ListedJournal] | None) -> list[Paper]:
    """Listed journals first (higher IF, then newer), then the rest by date."""

    def sort_key(paper: Paper) -> tuple[int, float, float]:
        listed = match_journal(paper, catalog) if catalog else None
        pri = 0 if listed else 1
        if_score = -(listed.if_2025 or 0.0) if listed else 0.0
        return (pri, if_score, -_paper_date_key(paper))

    return sorted(papers, key=sort_key)
