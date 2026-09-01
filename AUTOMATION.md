# Daily feed: Cursor Automation

要旨の日本語訳はエージェントが行う（DeepL は使わない）。GitHub Actions だけでは訳できないので、定期更新は **Cursor Automations** で回す。

このクラウドエージェントから Automation を新規作成する API はない。ダッシュボードか、手元 Cursor の `/automate` で作る。

## 「Environment」とは何か

GitHub の設定ではない。Cursor が毎回起こす **作業用マシンの中身** のこと。

- 毎日の Automation は、デフォルトだと **どの GitHub リポジトリもクローンしない**（Slack 通知だけならコードが要らないため）
- そのままだと `bibwatch run` も push もできない
- だから「この 3 つの GitHub リポジトリをマシンに置いて動かす」と指定する

| クローンする repo | 役割 |
|-------------------|------|
| `mizuy/bibwatch` | CLI |
| `mizuy/bibwatch-data` | watches / state（private） |
| `mizuy/bibwatch-feed` | 公開 RSS（Pages） |

やり方は次のどちらか。**A だけで足りることが多い。** A の画面に Environment を選べと出たら B を先にやる。

### A. Automation 作成画面で 3 つ選ぶ（先に試す）

1. Automations の新規作成を開く
2. Trigger を **Scheduled** にする（時刻は後述）
3. **Repository**（または Environment / Where should this run）を探す
4. 初期値の **No repository** のままにしない
5. **Multiple repositories**（または Multi-repo environment）を選ぶ
6. 上の 3 リポジトリにチェックを入れて保存

これで「3 つの repo を入れる」は完了。別画面で Environment を作る必要はない。

### B. A で Environment を先に作れと言われたとき

1. Cloud Agents ダッシュボード → **Environments** → 新規
2. GitHub 連携を求められたら接続する
3. リポジトリ選択で **同じ 3 つ** をまとめて選ぶ（1 つだけだと不足）
4. 名前は `bibwatch` でよい。Install は空でも、エージェントが `uv sync` する
5. 保存したら A に戻り、その Environment を選ぶ

Secrets の `BIBWATCH_FEED_TOKEN` は、この Environment か Automation の Runtime Secrets に置く。

## Secrets

| 名前 | 必須 | 内容 |
|------|------|------|
| `BIBWATCH_FEED_TOKEN` | **必須** | `state/feed-token` と同じ UUID。gitignore のため clone には入らない。未設定だと新しい UUID が作られ、購読 URL が壊れる |
| `NCBI_API_KEY` | 任意 | PubMed レート制限緩和 |

`DEEPL_API_KEY` は不要。

## Automation の残り

1. Trigger: **Scheduled** → cron `0 22 * * *`（UTC = 日本時間 07:00）
2. Repository: 上の A または B（単一 repo や No repository にしない）
3. Tools: Memories は任意。PR 作成ツールはデフォルト ON のままでよい（通常は main へ push し、拒否されたときだけ PR）
4. Prompt: 下のブロックをそのまま貼る
5. Save / Activate

手元の Cursor なら `/automate` に「毎日 UTC 22:00、bibwatch / bibwatch-data / bibwatch-feed の 3 リポジトリで daily ingest。プロンプトは AUTOMATION.md」と書けば同じ設定になる。

## 貼り付け用プロンプト

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

## 動作確認

- 初回は Automation 画面の **Run now** で一度回す
- 成功: `bibwatch-data` と `bibwatch-feed` の `main` に `feed: YYYY-MM-DD (N new)` が載る
- 新規ゼロかつ未訳なし: commit なしで終了してよい
- Pages: `https://mizuy.github.io/bibwatch-feed/feeds/<token>/all.xml` ほか `feeds.yaml` の各 XML
