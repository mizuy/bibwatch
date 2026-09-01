---
name: bibwatch-run
description: >-
  Run bibwatch poll/ingest/RSS publish on bibwatch-data. Use with Cursor Automation
  cron or manual ingest of new literature feeds.
---

# Bibwatch run

Daily scheduled runs: see `AUTOMATION.md` (Cursor Automation + paste-ready prompt).

## Prerequisites

1. cwd or `BIBWATCH_DATA` points at **bibwatch-data** (private repo)
2. `watches/*.yaml` configured
3. Optional `feeds.yaml` — named RSS files (default: `all.xml` + `priority.xml`)
4. Optional `journals.yaml` / `journals/*.yaml` — listed journals go to `priority.xml` and sort first in `all.xml`
5. Secrets: **`BIBWATCH_FEED_TOKEN` is required on Cloud Agents** (`state/feed-token` is gitignored and will not be in the clone)
6. Public feed checkout via `BIBWATCH_FEED` or `--feed-root` (sibling `bibwatch-feed` if present)

## Steps

1. `uv run bibwatch doctor` — fix blockers if any
2. `uv run bibwatch run --site-base https://<user>.github.io/bibwatch-feed`
3. `uv run bibwatch translate list --json` — abstracts still missing Japanese
4. **Translate those abstracts yourself** (Japanese, medical tone). Do **not** translate titles. Do **not** call DeepL.
5. Write a YAML file and apply:

   ```bash
   uv run bibwatch translate apply /tmp/translations.yaml
   uv run bibwatch publish --site-base https://<user>.github.io/bibwatch-feed
   ```

   YAML shape:

   ```yaml
   translations:
     - id: doi:10.example/x
       ja: |
         日本語の要旨。
   ```

6. If data `docs/` or `state/` changed: commit and push **bibwatch-data** `main`  
   message: `feed: YYYY-MM-DD (N new)`
7. If public `docs/feeds/` changed: commit and push **bibwatch-feed** `main` (same message). Pages is `main` / `/docs`.
8. If nothing changed: do not commit.
9. If `git push origin main` is rejected: open a PR with that title and say so.
10. Report: new paper count, how many abstracts were translated (do **not** log the full secret feed URL)

## Do not

- Change watch definitions unless asked
- Translate paper titles (abstract only)
- Use DeepL or any external translation API
- Expose watch theme names in commit messages or RSS categories
- Create a new feed token (always use `BIBWATCH_FEED_TOKEN`)
