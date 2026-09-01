"""Initialize bibwatch-data layout."""

from __future__ import annotations

import uuid
from pathlib import Path

from bibwatch.paths import (
    cursors_path,
    docs_dir,
    papers_dir,
    seen_path,
    state_dir,
    translations_dir,
    watches_dir,
)

DATA_GITIGNORE = """\
.venv/
state/feed-token
*.local.yaml
"""


def init_data_root(root: Path, *, feed_token: str | None = None) -> Path:
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    watches_dir(root).mkdir(exist_ok=True)
    state_dir(root).mkdir(exist_ok=True)
    papers_dir(root).mkdir(exist_ok=True)
    translations_dir(root).mkdir(exist_ok=True)
    docs_dir(root).mkdir(exist_ok=True)

    token = feed_token or str(uuid.uuid4())
    token_path = state_dir(root) / "feed-token"
    if not token_path.exists():
        token_path.write_text(token + "\n", encoding="utf-8")

    if not seen_path(root).exists():
        seen_path(root).write_text("", encoding="utf-8")

    if not cursors_path(root).exists():
        cursors_path(root).write_text("{}\n", encoding="utf-8")

    gi = root / ".gitignore"
    if not gi.exists():
        gi.write_text(DATA_GITIGNORE, encoding="utf-8")

    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(
            "# bibwatch-data\n\nPrivate watches and feed output for [bibwatch](https://github.com/mizuy/bibwatch).\n"
            "Enable GitHub Pages from `/docs` on this **private** repo.\n",
            encoding="utf-8",
        )

    return root
