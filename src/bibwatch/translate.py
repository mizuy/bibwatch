"""Translate paper abstracts (not titles)."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import yaml

from bibwatch.models import Paper
from bibwatch.paths import translations_dir


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


def translate_with_deepl(text: str, *, target_lang: str = "JA") -> str:
    api_key = os.environ.get("DEEPL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DEEPL_API_KEY is not set")
    base = "https://api-free.deepl.com" if api_key.endswith(":fx") else "https://api.deepl.com"
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            f"{base}/v2/translate",
            data={"auth_key": api_key, "text": text, "target_lang": target_lang, "source_lang": "EN"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["translations"][0]["text"]


def translate_paper_abstract(root: Path, paper: Paper, *, target: str = "ja", provider: str = "deepl") -> Paper:
    if not paper.abstract.original:
        return paper

    cached = load_translation_cache(root, paper.id)
    if cached and cached.get("abstract_ja"):
        paper.abstract.ja = cached["abstract_ja"]
        paper.abstract.translated = True
        return paper

    if provider != "deepl":
        return paper

    try:
        ja = translate_with_deepl(paper.abstract.original, target_lang="JA" if target == "ja" else target.upper())
        paper.abstract.ja = ja
        paper.abstract.translated = True
        save_translation_cache(
            root,
            paper.id,
            {
                "paper_id": paper.id,
                "abstract_original": paper.abstract.original,
                "abstract_ja": ja,
                "provider": provider,
            },
        )
    except RuntimeError:
        pass

    return paper
