# bibwatch-data

Private watches and ingest state. Pair with public [bibwatch](https://github.com/mizuy/bibwatch).

Free GitHub cannot serve Pages from a private repo. Keep this repo private and publish only `feeds/<token>/all.xml` to a **public** Pages site.

## Setup

1. Create **private** GitHub repo `bibwatch-data`
2. Copy this directory layout
3. `uv sync`
4. `uv run bibwatch init`
5. Add watches under `watches/`
6. Point `--pages-root` / `BIBWATCH_PAGES` at the public `bibwatch` checkout's `docs/`
7. Enable GitHub Pages on **public** `bibwatch`: `main` / `/docs`

## Feed URL

After `bibwatch run`:

```
https://<user>.github.io/bibwatch/feeds/<token>/all.xml
```

`<token>` = contents of `state/feed-token` (do not commit to public docs)

## Automation

See `AGENTS.md` and `skills/bibwatch-run/SKILL.md` in the bibwatch repo.
