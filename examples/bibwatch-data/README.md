# bibwatch-data

Private watches and RSS output. Pair with public [bibwatch](https://github.com/mizuy/bibwatch).

## Setup

1. Create **private** GitHub repo `bibwatch-data`
2. Copy this directory layout
3. `uv sync`
4. `uv run bibwatch init`
5. Add watches under `watches/`
6. GitHub Pages: Settings → Pages → `/docs`

## Feed URL

After `bibwatch run`:

```
https://<user>.github.io/bibwatch-data/feeds/<token>/all.xml
```

`<token>` = contents of `state/feed-token` (do not commit to public docs)

## Automation

See `AGENTS.md` and `skills/bibwatch-run/SKILL.md` in the bibwatch repo.
