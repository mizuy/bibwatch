## Automation: 新規文献 ingest

1. `uv run bibwatch run --site-base https://<user>.github.io --pages-root /path/to/public-pages`
2. 変更があれば commit & push
   - bibwatch-data: `docs/`, `state/`
   - 公開 Pages repo: `feeds/` のみ
3. commit message: `feed: YYYY-MM-DD (N new)` — watch 名を書かない

Secrets: `DEEPL_API_KEY`, `NCBI_API_KEY`（任意）, `BIBWATCH_FEED_TOKEN`（任意、`state/feed-token` でも可）
