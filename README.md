# Bibwatch

研究テーマを watch し、新着論文を enrich（雑誌・所属・国）→ abstract 訳 → **RSS** で配信する CLI。

**Bibliome とは完全独立。** ロジックはこの public repo、設定と feed は private **`bibwatch-data`** repo。

## 構成

| repo | 公開 | 内容 |
|------|------|------|
| **bibwatch** (この repo) | public | CLI・enrich・RSS 生成 |
| **bibwatch-data** | private | `watches/`, `state/`（Pages は使わない） |
| **公開 Pages サイト** | public | `feeds/<UUID>/all.xml` だけ置く |

## インストール

```bash
uv sync
uv run bibwatch --help
```

`bibwatch-data` 側:

```bash
cd bibwatch-data
uv add "bibwatch @ git+https://github.com/mizuy/bibwatch"
uv run bibwatch init
```

## 使い方

```bash
cd bibwatch-data
export BIBWATCH_DATA=$PWD
# または state/feed-token と DEEPL_API_KEY を Secrets に

uv run bibwatch watch list
uv run bibwatch poll --dry-run
uv run bibwatch run --site-base https://<user>.github.io --pages-root /path/to/public-pages
uv run bibwatch doctor
```

## RSS 配信

GitHub の無料プランは **private repo に Pages を置けない**。watch / state は private のまま、feed XML だけ公開サイトへ出す。

1. `bibwatch-data` は **private**（watch 定義・seen・papers）
2. 公開 Pages がある repo（ユーザーサイト `username.github.io` / `username.github.com`、または専用の public repo）に `feeds/<UUID>/all.xml` を置く
3. `BIBWATCH_PAGES` または `--pages-root` をその公開 checkout に向ける
4. feed URL（Inoreader 等）:

   `https://<user>.github.io/feeds/<UUID>/all.xml`

   UUID は `state/feed-token`（public README に書かない）

## RSS アイテム

| フィールド | 方針 |
|------------|------|
| `<title>` | 論文タイトル（**原文**） |
| `<description>` | 掲載誌・所属・国 + 訳アブスト + 原文 |

watch 名は RSS に出しません。

## Cursor Automation

private `bibwatch-data` と公開 Pages repo の両方を使う:

- cron: 1日1回
- install: `uv sync`
- 実行: `uv run bibwatch run --site-base https://<user>.github.io --pages-root /path/to/public-pages`
- push: data 側は `docs/`, `state/`。Pages 側は `feeds/` だけ

詳細: `skills/bibwatch-run/SKILL.md`

## Env

| Variable | Meaning |
|----------|---------|
| `BIBWATCH_DATA` | data ルート（未設定時 cwd） |
| `BIBWATCH_FEED_TOKEN` | feed UUID（未設定時 `state/feed-token`） |
| `BIBWATCH_PAGES` | 公開 Pages checkout（`feeds/<UUID>/all.xml` を書く） |
| `DEEPL_API_KEY` | abstract 翻訳（任意） |
| `NCBI_API_KEY` | PubMed enrich（任意） |

## Layout (bibwatch-data)

```text
watches/*.yaml
state/seen.jsonl
state/papers/
state/translations/
state/feed-token
docs/feeds/<UUID>/all.xml
```
