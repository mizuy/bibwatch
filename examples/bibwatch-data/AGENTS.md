## Automation: 新規文献 ingest

定期実行は Cursor Automation（親 repo の `AUTOMATION.md`）。作成画面で No repository をやめ、bibwatch / bibwatch-data / bibwatch-feed の 3 つを選ぶ。

1. `export BIBWATCH_FEED="${BIBWATCH_FEED:-$PWD/../bibwatch-feed}"`
2. `uv run bibwatch run --site-base https://<user>.github.io/bibwatch-feed`（`feeds.yaml` の各 XML。未定義時は `all.xml` + `priority.xml`）
3. 新規要旨をエージェントが日本語訳し、`bibwatch translate apply` → `bibwatch publish`
4. data 側に変更があれば commit & push **main**（`docs/`, `state/`）
5. `bibwatch-feed` の `docs/feeds/` が変わっていれば commit & push **main**
6. commit message: `feed: YYYY-MM-DD (N new)` — watch 名を書かない
7. 変更なしなら commit しない

Secrets: `BIBWATCH_FEED_TOKEN`（Cloud Agent では必須。`state/feed-token` は gitignore）, `NCBI_API_KEY`（任意）
