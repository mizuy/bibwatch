from pathlib import Path

from bibwatch.feeds import DEFAULT_FEEDS, load_feeds
from bibwatch.init_data import init_data_root
from bibwatch.journals import load_journal_catalog
from bibwatch.models import Journal, Paper
from bibwatch.run import papers_for_feed, run_all
from bibwatch.store import save_paper


def _paper(paper_id: str, journal: str, *, watches: list[str]) -> Paper:
    return Paper(
        id=paper_id,
        title=paper_id,
        watch_ids=watches,
        journal=Journal(name=journal, type="journal", published="2026-08-01"),
    )


def test_load_feeds_defaults(tmp_path: Path):
    assert [s.filename for s in load_feeds(tmp_path)] == ["all.xml", "priority.xml"]
    assert load_feeds(tmp_path)[0].id == DEFAULT_FEEDS[0].id


def test_load_feeds_yaml(tmp_path: Path):
    (tmp_path / "feeds.yaml").write_text(
        """
feeds:
  - id: susa
    filename: susa.xml
    title: SuSA
    watches: [w-susa]
    journals: false
  - id: major
    filename: major-gi.xml
    title: Major GI
    watches: [w-major-gi]
    journals: journals/major.yaml
    listed_only: true
""",
        encoding="utf-8",
    )
    specs = load_feeds(tmp_path)
    assert [s.id for s in specs] == ["susa", "major"]
    assert specs[0].journals is None
    assert specs[0].listed_only is False
    assert specs[1].journals == "journals/major.yaml"
    assert specs[1].listed_only is True


def test_papers_for_feed_filters_watch_and_journal(tmp_path: Path):
    init_data_root(tmp_path, feed_token="test-token-uuid-12345678")
    (tmp_path / "journals" ).mkdir()
    (tmp_path / "journals" / "major.yaml").write_text(
        """
journals:
  - name: The Lancet
    abbrev: Lancet
    if_2025: 109.0
""",
        encoding="utf-8",
    )
    (tmp_path / "feeds.yaml").write_text(
        """
feeds:
  - id: susa
    filename: susa.xml
    title: SuSA
    watches: [w-susa]
  - id: major
    filename: major-gi.xml
    title: Major GI
    watches: [w-major-gi]
    journals: journals/major.yaml
    listed_only: true
""",
        encoding="utf-8",
    )
    save_paper(tmp_path, _paper("doi:susa", "Gut", watches=["w-susa"]))
    save_paper(tmp_path, _paper("doi:rspo", "Gut", watches=["w-rspo"]))
    save_paper(tmp_path, _paper("doi:lancet", "The Lancet", watches=["w-major-gi"]))
    save_paper(tmp_path, _paper("doi:other", "Diagnostics", watches=["w-major-gi"]))

    specs = {s.id: s for s in load_feeds(tmp_path)}
    susa = papers_for_feed(tmp_path, specs["susa"])
    assert [p.id for p in susa] == ["doi:susa"]
    major = papers_for_feed(tmp_path, specs["major"])
    assert [p.id for p in major] == ["doi:lancet"]


def test_run_publishes_named_feeds(tmp_path: Path):
    init_data_root(tmp_path, feed_token="test-token-uuid-12345678")
    (tmp_path / "watches" / "w-test.yaml").write_text(
        "id: w-test\ntitle: Test\nenabled: false\nfeeds: []\n",
        encoding="utf-8",
    )
    (tmp_path / "feeds.yaml").write_text(
        """
feeds:
  - id: all
    filename: all.xml
    title: All
  - id: susa
    filename: susa.xml
    title: SuSA
    watches: [w-susa]
""",
        encoding="utf-8",
    )
    save_paper(tmp_path, _paper("doi:susa", "Gut", watches=["w-susa"]))
    feed_repo = tmp_path / "bibwatch-feed"
    result = run_all(tmp_path, feed_root=feed_repo, site_base="https://example.github.io/bibwatch-feed")
    names = {p.name for p in result.feed_paths}
    assert names == {"all.xml", "susa.xml"}
    public = feed_repo / "docs" / "feeds" / "test-token-uuid-12345678"
    assert (public / "susa.xml").is_file()
    xml = (public / "susa.xml").read_text(encoding="utf-8")
    assert "<title>SuSA</title>" in xml
    assert "doi:susa" in xml


def test_load_catalog_custom_path(tmp_path: Path):
    (tmp_path / "journals").mkdir()
    (tmp_path / "journals" / "major.yaml").write_text(
        "journals:\n  - name: Nature\n    if_2025: 56.1\n",
        encoding="utf-8",
    )
    catalog = load_journal_catalog(tmp_path, path="journals/major.yaml")
    assert catalog is not None
    assert catalog[0].name == "Nature"
    assert load_journal_catalog(tmp_path) is None
