"""Build a single static HTML page that shows every feed in a browser."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from bibwatch.feeds import FeedSpec
from bibwatch.journals import ListedJournal, match_journal
from bibwatch.models import Paper
from bibwatch.rss import journal_label

PAGE_FILENAME = "index.html"
# Group papers by the reader's calendar day (Japan).
DISPLAY_TZ = timezone(timedelta(hours=9))


@dataclass
class FeedPage:
    spec: FeedSpec
    papers: list[Paper]
    catalog: list[ListedJournal] | None = None


def added_date(paper: Paper) -> str:
    """The day (JST) bibwatch first saw the paper; falls back to the publication date."""
    if paper.fetched_at:
        try:
            dt = datetime.fromisoformat(paper.fetched_at.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(DISPLAY_TZ).date().isoformat()
        except ValueError:
            pass
    raw = paper.fetched_at or paper.journal.published or ""
    return raw[:10] if len(raw) >= 10 else ""


def _paper_link(paper: Paper) -> str | None:
    for key in ("doi", "landing", "pdf"):
        if paper.urls.get(key):
            return paper.urls[key]
    return None


def _paper_payload(paper: Paper) -> dict[str, Any]:
    out: dict[str, Any] = {
        "t": paper.title.strip() or "Untitled",
        "j": journal_label(paper),
        "p": paper.journal.published,
        "a": [a.name for a in paper.authors if a.name],
        "d": added_date(paper),
        "f": paper.fetched_at or "",
        "u": _paper_link(paper),
    }
    if paper.abstract.ja:
        out["ja"] = paper.abstract.ja
    if paper.abstract.original:
        out["en"] = paper.abstract.original
    if paper.ids.get("pmid"):
        out["pmid"] = paper.ids["pmid"]
    return {k: v for k, v in out.items() if v not in (None, "", [])}


def _feed_entries(page: FeedPage) -> list[list[Any]]:
    """[paper id, IF label or None] in display order: newest added day first.

    Within one day the feed's own order (listed journals, IF) is kept.
    """
    indexed = list(enumerate(page.papers))
    indexed.sort(key=lambda pair: (added_date(pair[1]), -pair[0]), reverse=True)
    rows: list[list[Any]] = []
    for _, paper in indexed:
        listed = match_journal(paper, page.catalog)
        badge = None
        if listed is not None:
            badge = f"IF {listed.if_2025:g}" if listed.if_2025 is not None else "優先誌"
        rows.append([paper.id, badge])
    return rows


def build_site(pages: list[FeedPage], *, title: str = "Bibwatch", generated_at: str | None = None) -> str:
    papers: dict[str, dict[str, Any]] = {}
    feeds: list[dict[str, Any]] = []
    for page in pages:
        for paper in page.papers:
            papers.setdefault(paper.id, _paper_payload(paper))
        feeds.append(
            {
                "id": page.spec.id,
                "title": page.spec.title,
                "desc": page.spec.description,
                "items": _feed_entries(page),
            }
        )
    # Derived from the data, not the clock, so an unchanged feed gives a byte-identical page
    # and the daily job still skips empty commits.
    latest = max((p.get("f", "") for p in papers.values()), default="")
    generated = generated_at or latest or "1970-01-01T00:00:00+00:00"
    data = {"generated": generated, "feeds": feeds, "papers": papers}
    # Keep "</script>" inside abstracts from closing the data block.
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (
        _TEMPLATE.replace("__TITLE__", html.escape(title))
        .replace("__DATA__", blob)
    )


_TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>__TITLE__</title>
<style>
:root {
  --bg: #fafaf8; --fg: #1d1d1f; --muted: #6b6b70; --line: #e4e4e0;
  --card: #ffffff; --accent: #2457c5; --new: #d4380d; --badge: #eef2fb;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #161618; --fg: #ececee; --muted: #9a9aa2; --line: #2c2c30;
    --card: #1e1e21; --accent: #7ea6ff; --new: #ff7a45; --badge: #243050;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--fg);
  font: 15px/1.6 -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Noto Sans JP", sans-serif;
}
header {
  position: sticky; top: 0; z-index: 1; background: var(--bg);
  border-bottom: 1px solid var(--line); padding: 10px 16px 0;
}
.bar { display: flex; gap: 8px; align-items: center; max-width: 860px; margin: 0 auto; }
.bar h1 { font-size: 17px; margin: 0; flex: 1; }
.bar input {
  flex: 0 1 220px; min-width: 0; padding: 6px 10px; font: inherit; color: var(--fg);
  background: var(--card); border: 1px solid var(--line); border-radius: 8px;
}
.bar button {
  flex: none; white-space: nowrap; padding: 6px 10px; font: inherit; font-size: 13px; color: var(--accent);
  background: none; border: 1px solid var(--line); border-radius: 8px; cursor: pointer;
}
nav {
  display: flex; gap: 4px; overflow-x: auto; max-width: 860px; margin: 8px auto 0;
  scrollbar-width: none;
}
nav button {
  flex: none; padding: 6px 10px 8px; font: inherit; font-size: 14px; color: var(--muted);
  background: none; border: 0; border-bottom: 2px solid transparent; cursor: pointer;
}
nav button[aria-selected="true"] { color: var(--fg); border-bottom-color: var(--accent); font-weight: 600; }
nav .count { font-size: 12px; color: var(--new); margin-left: 3px; }
main { max-width: 860px; margin: 0 auto; padding: 8px 16px 48px; }
.desc { color: var(--muted); font-size: 13px; margin: 8px 0 0; }
h2 { font-size: 13px; color: var(--muted); font-weight: 600; margin: 20px 0 6px; }
article {
  background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 12px 14px; margin-bottom: 8px;
}
article.new { border-left: 3px solid var(--new); }
.title { font-weight: 600; color: var(--fg); text-decoration: none; }
.title:hover { color: var(--accent); }
.meta { font-size: 13px; color: var(--muted); margin-top: 4px; }
.tag {
  display: inline-block; font-size: 11px; font-weight: 600; padding: 0 6px; border-radius: 4px;
  margin-right: 6px; vertical-align: 2px;
}
.tag.new { color: #fff; background: var(--new); }
.tag.if { color: var(--accent); background: var(--badge); }
details { margin-top: 6px; font-size: 14px; }
summary { cursor: pointer; color: var(--accent); font-size: 13px; }
details p { margin: 6px 0 0; white-space: pre-wrap; }
details .en { color: var(--muted); font-size: 13px; }
details a { color: var(--accent); }
.empty, footer { color: var(--muted); font-size: 13px; text-align: center; margin-top: 32px; }
</style>
</head>
<body>
<header>
  <div class="bar">
    <h1>__TITLE__</h1>
    <input id="q" type="search" placeholder="検索" aria-label="検索">
    <button id="read" type="button" title="NEW 印をすべて消す">既読にする</button>
  </div>
  <nav id="tabs" role="tablist"></nav>
</header>
<main id="list"></main>
<footer id="foot"></footer>
<script id="data" type="application/json">__DATA__</script>
<script>
(function () {
  var DATA = JSON.parse(document.getElementById("data").textContent);
  var KEY = "bibwatch:";
  function load(k) { try { return localStorage.getItem(KEY + k); } catch (e) { return null; } }
  function save(k, v) { try { localStorage.setItem(KEY + k, v); } catch (e) {} }

  // A visit more than 30 minutes after the last one moves the "seen up to" mark,
  // so reloading the page keeps the NEW marks. A first visit shows the last 3 days as NEW.
  var now = new Date().toISOString();
  var last = load("lastVisit");
  var seenUpTo = load("seenUpTo");
  if (!last) { seenUpTo = new Date(Date.parse(DATA.generated) - 3 * 86400000).toISOString(); }
  else if (Date.parse(now) - Date.parse(last) > 30 * 60 * 1000) { seenUpTo = last; }
  save("lastVisit", now);
  if (seenUpTo) save("seenUpTo", seenUpTo);
  var seenMs = Date.parse(seenUpTo) || 0;

  function isNew(p) { return !!(p.f && Date.parse(p.f) > seenMs); }

  var feeds = DATA.feeds;
  var current = load("tab");
  if (!feeds.some(function (f) { return f.id === current; })) current = feeds.length ? feeds[0].id : null;

  var tabs = document.getElementById("tabs");
  var list = document.getElementById("list");
  var q = document.getElementById("q");

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function renderTabs() {
    tabs.textContent = "";
    feeds.forEach(function (f) {
      var b = el("button", null, f.title);
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", f.id === current ? "true" : "false");
      var n = f.items.filter(function (it) { return isNew(DATA.papers[it[0]]); }).length;
      if (n) b.appendChild(el("span", "count", String(n)));
      b.onclick = function () { current = f.id; save("tab", current); render(); };
      tabs.appendChild(b);
    });
  }

  function matches(p, words) {
    if (!words.length) return true;
    var hay = [p.t, p.j, (p.a || []).join(" "), p.ja, p.en].join(" ").toLowerCase();
    return words.every(function (w) { return hay.indexOf(w) >= 0; });
  }

  function card(p, badge) {
    var a = el("article", isNew(p) ? "new" : null);
    var head = el("div");
    if (isNew(p)) head.appendChild(el("span", "tag new", "NEW"));
    if (badge) head.appendChild(el("span", "tag if", badge));
    var t = el(p.u ? "a" : "span", "title", p.t);
    if (p.u) { t.href = p.u; t.target = "_blank"; t.rel = "noopener"; }
    head.appendChild(t);
    a.appendChild(head);
    var bits = [p.j, p.p].filter(Boolean);
    var authors = p.a || [];
    if (authors.length) bits.push(authors.length > 3 ? authors.slice(0, 3).join(", ") + " ほか" : authors.join(", "));
    a.appendChild(el("div", "meta", bits.join(" · ")));
    if (p.ja || p.en) {
      var d = el("details");
      d.appendChild(el("summary", null, p.ja ? "要旨" : "Abstract"));
      if (p.ja) d.appendChild(el("p", null, p.ja));
      if (p.en) d.appendChild(el("p", p.ja ? "en" : null, p.en));
      if (p.pmid) {
        var link = el("a", null, "PubMed " + p.pmid);
        link.href = "https://pubmed.ncbi.nlm.nih.gov/" + p.pmid + "/";
        link.target = "_blank"; link.rel = "noopener";
        var lp = el("p", "en"); lp.appendChild(link); d.appendChild(lp);
      }
      a.appendChild(d);
    }
    return a;
  }

  function render() {
    renderTabs();
    list.textContent = "";
    var f = feeds.filter(function (x) { return x.id === current; })[0];
    if (!f) { list.appendChild(el("p", "empty", "フィードがありません")); return; }
    if (f.desc) list.appendChild(el("p", "desc", f.desc));
    var words = q.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);
    var day = null, shown = 0;
    f.items.forEach(function (it) {
      var p = DATA.papers[it[0]];
      if (!p || !matches(p, words)) return;
      if (p.d !== day) { day = p.d; list.appendChild(el("h2", null, day ? day + " に追加" : "日付不明")); }
      list.appendChild(card(p, it[1]));
      shown++;
    });
    if (!shown) list.appendChild(el("p", "empty", "該当する論文はありません"));
  }

  q.oninput = render;
  document.getElementById("read").onclick = function () {
    seenUpTo = new Date().toISOString();
    save("seenUpTo", seenUpTo);
    seenMs = Date.parse(seenUpTo);
    render();
  };
  document.getElementById("foot").textContent = "最終追加: " + new Date(DATA.generated).toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" });
  render();
})();
</script>
</body>
</html>
"""
