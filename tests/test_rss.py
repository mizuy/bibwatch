"""Tests for RSS generation."""

from xml.etree import ElementTree as ET

from bibwatch.models import Abstract, Affiliation, Author, Journal, Paper
from bibwatch.rss import build_rss, item_title, year_month


def _paper() -> Paper:
    return Paper(
        id="doi:10.1038/test",
        title="Original English Title",
        authors=[
            Author(name="Saito Yutaka", last="Saito", first="Yutaka"),
            Author(name="Abe Seiichiro", last="Abe", first="Seiichiro"),
        ],
        journal=Journal(name="Nature", published="2026-08-30"),
        affiliations=[Affiliation(institution="MIT", country="アメリカ", country_code="US")],
        abstract=Abstract(original="We did science.", ja="科学をした。", translated=True),
        urls={"doi": "https://doi.org/10.1038/test"},
        ids={"doi": "10.1038/test"},
    )


def test_item_title_includes_journal_and_year_month():
    assert item_title(_paper()) == "Original English Title / Nature / 2026-08"
    assert year_month("2026") == "2026"
    assert year_month(None) is None


def test_build_rss_title_and_authors():
    xml = build_rss(
        [_paper()],
        feed_title="Test Feed",
        feed_link="https://example.com/feed",
        feed_description="d",
    )
    channel = ET.fromstring(xml).find("channel")
    assert channel is not None
    assert channel.findtext("title") == "Test Feed"
    item = channel.find("item")
    assert item is not None
    assert item.findtext("title") == "Original English Title / Nature / 2026-08"
    desc = item.findtext("description") or ""
    assert "著者" in desc
    assert "Saito Yutaka" in desc
    assert "Abe Seiichiro" in desc
    assert "要旨（訳）" in desc
    assert "掲載誌" in desc
    assert "MIT" in desc
    assert "crispr" not in desc.lower()
