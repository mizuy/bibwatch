"""Tests for RSS generation."""

from bibwatch.models import Abstract, Affiliation, Journal, Paper
from bibwatch.rss import build_rss


def test_build_rss_title_original():
    paper = Paper(
        id="doi:10.1038/test",
        title="Original English Title",
        journal=Journal(name="Nature", published="2026-08-30"),
        affiliations=[Affiliation(institution="MIT", country="アメリカ", country_code="US")],
        abstract=Abstract(original="We did science.", ja="科学をした。", translated=True),
        urls={"doi": "https://doi.org/10.1038/test"},
        ids={"doi": "10.1038/test"},
    )
    xml = build_rss([paper], feed_title="Test", feed_link="https://example.com/feed", feed_description="d")
    assert "<title>Original English Title</title>" in xml
    assert "要旨（訳）" in xml
    assert "掲載誌" in xml
    assert "MIT" in xml
    assert "crispr" not in xml.lower()
