# bibwatch-data

Private watches and state. Pair with public [bibwatch](https://github.com/mizuy/bibwatch) and public [bibwatch-feed](https://github.com/mizuy/bibwatch-feed).

## Setup

1. Create **private** GitHub repo `bibwatch-data`
2. Create **public** GitHub repo `bibwatch-feed`
3. Copy this directory layout
4. `uv sync`
5. `uv run bibwatch init`
6. Add watches under `watches/`
7. Optional: `feeds.yaml` (named RSS files; default all.xml + priority.xml)
8. Optional: `journals.yaml` (priority.xml + sort-first in all.xml)
9. GitHub Pages: on **bibwatch-feed**, Settings → Pages → `main` / `/docs`

## Feed URL

After `bibwatch run` with `BIBWATCH_FEED` pointing at the `bibwatch-feed` checkout:

```
https://<user>.github.io/bibwatch-feed/feeds/<token>/all.xml
```

`<token>` = contents of `state/feed-token` (do not put the full URL in public README)

## Automation

See `AGENTS.md` and `skills/bibwatch-run/SKILL.md` in the bibwatch repo.
