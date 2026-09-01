"""Resolve bibwatch-data root and standard directories."""

from __future__ import annotations

import os
from pathlib import Path

ENV_DATA_ROOT = "BIBWATCH_DATA"
ENV_FEED_TOKEN = "BIBWATCH_FEED_TOKEN"


def resolve_data_root(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    env = os.environ.get(ENV_DATA_ROOT)
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()


def watches_dir(root: Path) -> Path:
    return root / "watches"


def state_dir(root: Path) -> Path:
    return root / "state"


def papers_dir(root: Path) -> Path:
    return state_dir(root) / "papers"


def translations_dir(root: Path) -> Path:
    return state_dir(root) / "translations"


def seen_path(root: Path) -> Path:
    return state_dir(root) / "seen.jsonl"


def cursors_path(root: Path) -> Path:
    return state_dir(root) / "cursors.yaml"


def docs_dir(root: Path) -> Path:
    return root / "docs"


def feed_token(root: Path) -> str:
    env = os.environ.get(ENV_FEED_TOKEN, "").strip()
    if env:
        return env
    token_file = state_dir(root) / "feed-token"
    if token_file.is_file():
        return token_file.read_text(encoding="utf-8").strip()
    raise FileNotFoundError(
        f"Feed token not found. Set {ENV_FEED_TOKEN} or create {token_file} "
        "(run `bibwatch init` to generate one)."
    )


def feed_publish_dir(root: Path) -> Path:
    return docs_dir(root) / "feeds" / feed_token(root)
