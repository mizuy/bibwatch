# Daily feed: Cursor Automation

要旨の日本語訳はエージェントが行う（DeepL は使わない）。GitHub Actions だけでは訳できないので、定期更新は **Cursor Automations**（[cursor.com/automations](https://cursor.com/automations)）で回す。

このクラウドエージェントから Automation を新規作成する API はない。ダッシュボードか、手元 Cursor の `/automate` で作る。

## 1. Cloud Agents 環境（必須・複数 repo）

cron はデフォルトで **リポジトリなし**。コードを書いて push するには環境を明示する。

[Cloud Agents の Environments](https://cursor.com/dashboard?tab=cloud-agents) で次の 3 つを同じ環境に入れる。

| repo | 役割 |
|------|------|
| [mizuy/bibwatch](https://github.com/mizuy/bibwatch) | CLI |
| [mizuy/bibwatch-data](https://github.com/mizuy/bibwatch-data) | watches / state（private） |
| [mizuy/bibwatch-feed](https://github.com/mizuy/bibwatch-feed) | 公開 RSS（Pages） |

Install（環境の `install`、または data 側 `.cursor/environment.json`）:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
cd bibwatch-data && uv sync
```

Egress を絞る場合は少なくとも `eutils.ncbi.nlm.nih.gov`、`api.openalex.org`、`github.com`、`api.github.com` を許可する。

## 2. Runtime Secrets

Cloud Agents の Runtime Secrets（Automation 作成画面でも可）。

| 名前 | 必須 | 内容 |
|------|------|------|
| `BIBWATCH_FEED_TOKEN` | **必須** | `state/feed-token` と同じ UUID。gitignore のため clone には入らない。未設定だと新しい UUID が作られ、購読 URL が壊れる |
| `NCBI_API_KEY` | 任意 | PubMed レート制限緩和 |

`DEEPL_API_KEY` は不要。

## 3. Automation を作る

1. [cursor.com/automations/new](https://cursor.com/automations/new)
2. Trigger: **Scheduled** → cron `0 22 * * *`（UTC = 日本時間 07:00）
3. Repository: 上の **multi-repo 環境**（単一 repo や「なし」にしない）
4. Tools: Memories は任意。PR 作成ツールはデフォルト ON のままでよい（通常は main へ push し、拒否されたときだけ PR）
5. Prompt: 下のブロックをそのまま貼る
6. Save / Activate

手元の Cursor なら `/automate` に「毎日 UTC 22:00、3 repo 環境で bibwatch の daily ingest。プロンプトは bibwatch の AUTOMATION.md」と書けば同じ設定になる。

## 4. 貼り付け用プロンプト

```
You run the daily bibwatch literature ingest. Follow skills/bibwatch-run/SKILL.md and bibwatch-data/AGENTS.md.

Repos (must all be present as siblings, e.g. under /workspace or /agent/repos):
- bibwatch (CLI)
- bibwatch-data (private watches + state)
- bibwatch-feed (public GitHub Pages RSS)

Do not change watches/*.yaml, feeds.yaml, journals, or CLI code unless this run's user message explicitly asks.

Steps:
1. Find the checkouts. export BIBWATCH_DATA=<bibwatch-data> and BIBWATCH_FEED=<bibwatch-feed>.
2. cd "$BIBWATCH_DATA" && uv sync && uv run bibwatch doctor
3. uv run bibwatch run --site-base https://mizuy.github.io/bibwatch-feed
4. uv run bibwatch translate list --json
5. Translate missing abstracts yourself into Japanese (medical tone). Never translate titles. Never call DeepL or any translation API.
6. Write YAML and apply:
     translations:
       - id: <paper id>
         ja: |
           ...
   then: uv run bibwatch translate apply /tmp/translations.yaml
   then: uv run bibwatch publish --site-base https://mizuy.github.io/bibwatch-feed
7. If nothing changed in bibwatch-data (docs/ or state/) and nothing changed in bibwatch-feed (docs/feeds/), stop. No empty commit, no PR.
8. If feed/state files changed: commit and push **directly to origin/main** on each repo that changed. Pages only serves bibwatch-feed main /docs.
   - bibwatch-data: git add docs state && git commit -m "feed: YYYY-MM-DD (N new)" && git push origin main
   - bibwatch-feed: git add docs/feeds && git commit -m "feed: YYYY-MM-DD (N new)" && git push origin main
   Do not put watch names, theme names, or the feed token in commit messages or the run summary.
9. If push to main is rejected, open a PR with the same commit message as the title and say so in the summary.
10. Summary: new paper count, abstracts translated, whether main was updated. Do not print the full secret feed URL.
```

## 5. 動作確認

- 初回は Automation 画面の **Run now** で一度回す
- 成功: `bibwatch-data` と `bibwatch-feed` の `main` に `feed: YYYY-MM-DD (N new)` が載る
- 新規ゼロかつ未訳なし: commit なしで終了してよい
- Pages: `https://mizuy.github.io/bibwatch-feed/feeds/<token>/all.xml` ほか `feeds.yaml` の各 XML
