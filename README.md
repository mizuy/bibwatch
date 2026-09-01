# Bibwatch

研究テーマを watch し、新着論文を enrich（雑誌・所属・国）→ abstract 訳 → **RSS** で配信する CLI。

**Bibliome とは完全独立。** ロジックはこの public repo、設定は private **`bibwatch-data`**、RSS は public **`bibwatch-feed`**。

## 構成

| repo | 公開 | 内容 |
|------|------|------|
| **bibwatch** (この repo) | public | CLI・enrich・RSS 生成 |
| **bibwatch-data** | private | `watches/`, `state/`（Pages は使わない） |
| **bibwatch-feed** | public | `docs/feeds/<UUID>/all.xml`（GitHub Pages） |

GitHub の無料プランは **private repo に Pages を置けない**。feed XML だけ public の `bibwatch-feed` へ出す。

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
export BIBWATCH_FEED=/path/to/bibwatch-feed
# または state/feed-token と DEEPL_API_KEY を Secrets に

uv run bibwatch watch list
uv run bibwatch poll --dry-run
uv run bibwatch run --site-base https://<user>.github.io/bibwatch-feed
uv run bibwatch doctor
```

## RSS 配信

1. `bibwatch-data` は **private**（watch 定義・seen・papers）
2. `bibwatch-feed` は **public**。`BIBWATCH_FEED` / `--feed-root` をその checkout に向ける
3. GitHub Pages: `bibwatch-feed` の Settings → Pages → `main` / `/docs`
4. feed URL（Inoreader 等）:

   `https://<user>.github.io/bibwatch-feed/feeds/<UUID>/all.xml`

   UUID は `state/feed-token`（README 本文には書かない）

Pages を付ける前でも raw で購読できる。

`https://raw.githubusercontent.com/<user>/bibwatch-feed/main/docs/feeds/<UUID>/all.xml`

## RSS アイテム

| フィールド | 方針 |
|------------|------|
| `<title>` | 論文タイトル（**原文**） |
| `<description>` | 掲載誌・所属・国 + 訳アブスト + 原文 |

watch 名は RSS に出しません。

## Cursor Automation

private `bibwatch-data` と public `bibwatch-feed` の両方を使う:

- cron: 1日1回
- install: `uv sync`
- 実行: `uv run bibwatch run --site-base https://<user>.github.io/bibwatch-feed`
- push: data 側は `docs/`, `state/`。`bibwatch-feed` は `docs/feeds/`

詳細: `skills/bibwatch-run/SKILL.md`

## Env

| Variable | Meaning |
|----------|---------|
| `BIBWATCH_DATA` | data ルート（未設定時 cwd） |
| `BIBWATCH_FEED` | public `bibwatch-feed` checkout（`docs/feeds/<UUID>/all.xml` を書く） |
| `BIBWATCH_FEED_TOKEN` | feed UUID（未設定時 `state/feed-token`） |
| `DEEPL_API_KEY` | abstract 翻訳（任意） |
| `NCBI_API_KEY` | PubMed enrich（任意） |

## Layout (bibwatch-data)

```text
watches/*.yaml
state/seen.jsonl
state/papers/
state/translations/
state/feed-token
docs/feeds/<UUID>/all.xml   # ローカル控え
```

## Layout (bibwatch-feed)

```text
docs/.nojekyll
docs/feeds/<UUID>/all.xml   # GitHub Pages で公開
```
