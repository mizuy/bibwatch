## Automation: 新規文献 ingest

1. `export BIBWATCH_FEED="${BIBWATCH_FEED:-$PWD/../bibwatch-feed}"`
2. `uv run bibwatch run --site-base https://<user>.github.io/bibwatch-feed`
3. data 側に変更があれば commit & push（`docs/`, `state/`）
4. `bibwatch-feed` の `docs/feeds/` が変わっていれば commit & push
5. commit message: `feed: YYYY-MM-DD (N new)` — watch 名を書かない

Secrets: `DEEPL_API_KEY`, `NCBI_API_KEY`（任意）, `BIBWATCH_FEED_TOKEN`（任意、`state/feed-token` でも可）
