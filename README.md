# Bibwatch

研究テーマを watch し、新着論文を enrich（雑誌・所属・国）→ abstract 訳 → **RSS** で配信する CLI。

**Bibliome とは完全独立。** ロジックはこの public repo、設定は private **`bibwatch-data`**、RSS は public **`bibwatch-feed`**。

## 構成

| repo | 公開 | 内容 |
|------|------|------|
| **bibwatch** (この repo) | public | CLI・enrich・RSS 生成 |
| **bibwatch-data** | private | `watches/`, `feeds.yaml`, `journals.yaml`, `state/`（Pages は使わない） |
| **bibwatch-feed** | public | `docs/feeds/<UUID>/*.xml`（GitHub Pages） |

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
# または state/feed-token を Secrets に

uv run bibwatch watch list
uv run bibwatch poll --dry-run
uv run bibwatch run --site-base https://<user>.github.io/bibwatch-feed
uv run bibwatch translate list
uv run bibwatch publish --site-base https://<user>.github.io/bibwatch-feed
uv run bibwatch doctor
```

## RSS 配信

1. `bibwatch-data` は **private**（watch 定義・seen・papers）
2. `bibwatch-feed` は **public**。`BIBWATCH_FEED` / `--feed-root` をその checkout に向ける
3. GitHub Pages: `bibwatch-feed` の Settings → Pages → `main` / `/docs`
4. feed URL（Inoreader 等）:

   `https://<user>.github.io/bibwatch-feed/feeds/<UUID>/all.xml`  
   `https://<user>.github.io/bibwatch-feed/feeds/<UUID>/priority.xml`（指定誌）  
   ほか `feeds.yaml` で定義した `*.xml`（例: `major-gi.xml`）

   UUID は `state/feed-token`（README 本文には書かない）

Pages を付ける前でも raw で購読できる。

`https://raw.githubusercontent.com/<user>/bibwatch-feed/main/docs/feeds/<UUID>/all.xml`

## RSS アイテム

| フィールド | 方針 |
|------------|------|
| `<title>` | 論文タイトル（原文） / 雑誌 / 年月 |
| `<description>` | 掲載誌（IF 2025）・著者・所属・国 + 訳アブスト（エージェント） + 原文 |

watch 名は RSS アイテムに出しません。`journals.yaml` がある場合、指定誌を **priority.xml** に出し、`all.xml` では指定誌を先に並べます（他誌も残す）。追加の名前付き feed は `feeds.yaml` で定義します（watch の絞り込み・別ジャーナル表・`listed_only`）。

## Cursor Automation

private `bibwatch-data` と public `bibwatch-feed` の両方を使う:

- cron: 1日1回
- install: `uv sync`
- 実行: `uv run bibwatch run` → 新規要旨を日本語訳 → `translate apply` → `publish`
- push: data 側は `docs/`, `state/`。`bibwatch-feed` は `docs/feeds/`

詳細: `skills/bibwatch-run/SKILL.md`

## Env

| Variable | Meaning |
|----------|---------|
| `BIBWATCH_DATA` | data ルート（未設定時 cwd） |
| `BIBWATCH_FEED` | public `bibwatch-feed` checkout（`docs/feeds/<UUID>/all.xml` を書く） |
| `BIBWATCH_FEED_TOKEN` | feed UUID（未設定時 `state/feed-token`） |
| `NCBI_API_KEY` | PubMed enrich（任意） |

## Layout (bibwatch-data)

```text
watches/*.yaml
feeds.yaml                  # 名前付き RSS（省略時は all + priority）
journals.yaml               # 優先ジャーナル（all + priority）
journals/*.yaml             # feed ごとのジャーナル表（任意）
state/seen.jsonl
state/papers/
state/translations/
state/feed-token
docs/feeds/<UUID>/*.xml     # ローカル控え
```

## Layout (bibwatch-feed)

```text
docs/.nojekyll
docs/feeds/<UUID>/*.xml     # GitHub Pages で公開
```
