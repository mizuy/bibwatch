"""Tests for the static HTML page."""

import json
import re

from bibwatch.feeds import FeedSpec
from bibwatch.journals import ListedJournal
from bibwatch.models import Abstract, Author, Journal, Paper
from bibwatch.site import FeedPage, build_site


def _paper(pid: str, journal: str, fetched: str, **kw) -> Paper:
    return Paper(
        id=pid,
        title=kw.get("title", f"Title {pid}"),
        authors=[Author(name="Saito Yutaka")],
        journal=Journal(name=journal, published="2026-10-01"),
        abstract=kw.get("abstract", Abstract()),
        urls={"doi": f"https://doi.org/{pid}"},
        ids={"pmid": "123"},
        fetched_at=fetched,
    )


def _data(page: str) -> dict:
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S)
    assert m
    return json.loads(m.group(1))


def test_build_site_orders_by_added_day_then_feed_order():
    papers = [
        _paper("doi:old-high", "Gut", "2026-10-20T18:00:00+00:00"),
        _paper("doi:new-high", "Gut", "2026-10-31T18:00:00+00:00"),
        _paper("doi:new-low", "Other", "2026-10-31T18:00:00+00:00"),
    ]
    catalog = [ListedJournal(name="Gut", if_2025=25.8)]
    page = build_site(
        [FeedPage(spec=FeedSpec(id="all", filename="all.xml", title="All"), papers=papers, catalog=catalog)],
        generated_at="2026-11-01T00:00:00+00:00",
    )
    data = _data(page)
    items = data["feeds"][0]["items"]
    assert [i[0] for i in items] == ["doi:new-high", "doi:new-low", "doi:old-high"]
    assert items[0][1] == "IF 25.8"
    assert items[1][1] is None
    # 18:00 UTC is 03:00 the next day in Japan.
    assert data["papers"]["doi:new-high"]["d"] == "2026-11-01"


def test_build_site_shares_papers_across_feeds_and_escapes_script():
    p = _paper(
        "doi:x",
        "Gut",
        "2026-10-31T18:00:00+00:00",
        title="A </script><b>bad</b>",
        abstract=Abstract(original="EN", ja="日本語"),
    )
    page = build_site(
        [
            FeedPage(spec=FeedSpec(id="a", filename="a.xml", title="A"), papers=[p]),
            FeedPage(spec=FeedSpec(id="b", filename="b.xml", title="B"), papers=[p]),
        ]
    )
    assert page.count("</script>") == 2  # data block + app script only
    data = _data(page)
    assert list(data["papers"]) == ["doi:x"]
    assert data["papers"]["doi:x"]["ja"] == "日本語"
    assert data["papers"]["doi:x"]["t"] == "A </script><b>bad</b>"
    assert [f["id"] for f in data["feeds"]] == ["a", "b"]


def test_build_site_is_stable_for_same_data():
    pages = [
        FeedPage(
            spec=FeedSpec(id="a", filename="a.xml", title="A"),
            papers=[_paper("doi:x", "Gut", "2026-10-31T18:00:00+00:00")],
        )
    ]
    first = build_site(pages)
    assert first == build_site(pages)
    assert _data(first)["generated"] == "2026-10-31T18:00:00+00:00"
