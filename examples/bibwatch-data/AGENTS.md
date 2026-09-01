## Automation: 新規文献 ingest

1. `export BIBWATCH_FEED="${BIBWATCH_FEED:-$PWD/../bibwatch-feed}"`
2. `uv run bibwatch run --site-base https://<user>.github.io/bibwatch-feed`（`feeds.yaml` の各 XML。未定義時は `all.xml` + `priority.xml`）
3. 新規要旨をエージェントが日本語訳し、`bibwatch translate apply` → `bibwatch publish`
4. data 側に変更があれば commit & push（`docs/`, `state/`）
5. `bibwatch-feed` の `docs/feeds/` が変わっていれば commit & push
6. commit message: `feed: YYYY-MM-DD (N new)` — watch 名を書かない

Secrets: `NCBI_API_KEY`（任意）, `BIBWATCH_FEED_TOKEN`（任意、`state/feed-token` でも可）
