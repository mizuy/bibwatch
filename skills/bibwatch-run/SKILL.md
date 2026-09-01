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
3. Secrets: `DEEPL_API_KEY` (optional), `BIBWATCH_FEED_TOKEN` or `state/feed-token`
4. Public Pages checkout via `BIBWATCH_PAGES` or `--pages-root` (free GitHub cannot host Pages on a private repo)

## Steps

1. `uv run bibwatch doctor` — fix blockers if any
2. `uv run bibwatch run --site-base https://<user>.github.io --pages-root /path/to/public-pages`
3. If `docs/` or `state/` changed: commit and push **bibwatch-data** `main`
4. If `feeds/` changed: commit and push the **public Pages** repo
5. Report: new paper count, feed path (do **not** log full secret URL in public artifacts)

## Do not

- Change watch definitions unless asked
- Translate paper titles (abstract only)
- Expose watch theme names in commit messages or RSS categories
