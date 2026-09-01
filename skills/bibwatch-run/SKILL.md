---
name: bibwatch-run
description: >-
  Run bibwatch poll/ingest/RSS publish on bibwatch-data. Use with Cursor Automation
  cron or manual ingest of new literature feeds.
---

# Bibwatch run

## Prerequisites

1. cwd or `BIBWATCH_DATA` points at **bibwatch-data** (private repo)
2. `watches/*.yaml` configured
3. Optional `journals.yaml` allowlist — if present, RSS includes only those journals
4. Secrets: `DEEPL_API_KEY` (optional), `BIBWATCH_FEED_TOKEN` or `state/feed-token`
5. Public feed checkout via `BIBWATCH_FEED` or `--feed-root` (sibling `bibwatch-feed` if present)

## Steps

1. `uv run bibwatch doctor` — fix blockers if any
2. `uv run bibwatch run --site-base https://<user>.github.io/bibwatch-feed`
3. If data `docs/` or `state/` changed: commit and push **bibwatch-data** `main`
4. If public `docs/feeds/` changed: commit and push **bibwatch-feed**
5. Report: new paper count, feed path (do **not** log full secret URL in public artifacts)

## Do not

- Change watch definitions unless asked
- Translate paper titles (abstract only)
- Expose watch theme names in commit messages or RSS categories
