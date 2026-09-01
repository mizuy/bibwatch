# Bibwatch — tool repo

CLI 実装と Agent skill の置き場。データは **bibwatch-data**（private）。RSS 配信は **bibwatch-feed**（public）。

- 実装変更: この repo
- watch 定義・指定ジャーナル・state: bibwatch-data
- RSS 公開: bibwatch-feed（`docs/feeds/<token>/`）
- 日常: `cd bibwatch-data && uv run bibwatch run --site-base https://<user>.github.io/bibwatch-feed`
