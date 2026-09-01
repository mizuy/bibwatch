from pathlib import Path

from bibwatch.journals import (
    ListedJournal,
    filter_listed_papers,
    load_journal_catalog,
    match_journal,
    normalize_journal_name,
)
from bibwatch.models import Journal, Paper
from bibwatch.rss import build_rss


def _paper(name: str, *, iso: str | None = None, paper_id: str = "doi:1") -> Paper:
    return Paper(
        id=paper_id,
        title="T",
        journal=Journal(name=name, iso_abbrev=iso, type="journal"),
    )


def test_normalize_strips_the_and_punctuation():
    assert normalize_journal_name("The American Journal of Gastroenterology") == (
        "american journal of gastroenterology"
    )
    assert normalize_journal_name("Lancet Gastroenterology & Hepatology") == (
        normalize_journal_name("\u0098The \u009cLancet. Gastroenterology & hepatology")
    )
    assert normalize_journal_name("Gastroenterology") != normalize_journal_name(
        "Gastroenterology Report"
    )


def test_match_name_abbrev_and_exactness():
    catalog = [
        ListedJournal(name="American Journal of Gastroenterology", abbrev="Am J Gastroenterol", if_2025=8.5),
        ListedJournal(name="Gastroenterology", abbrev="Gastroenterology", if_2025=29.7),
        ListedJournal(name="Oncology", abbrev="Oncology", if_2025=1.6, if_2025_flag="*"),
    ]
    assert match_journal(_paper("The American Journal of Gastroenterology"), catalog).name.startswith(
        "American"
    )
    assert match_journal(_paper("Am J Gastroenterol"), catalog).abbrev == "Am J Gastroenterol"
    assert match_journal(_paper("Gastroenterology"), catalog).if_2025 == 29.7
    assert match_journal(_paper("Gastroenterology Report"), catalog) is None
    assert match_journal(_paper("Frontiers in Oncology"), catalog) is None
    assert match_journal(_paper("Oncology"), catalog).if_2025_flag == "*"
    assert match_journal(_paper("arXiv", paper_id="arxiv:1"), catalog) is None


def test_load_catalog_and_filter(tmp_path: Path):
    (tmp_path / "journals.yaml").write_text(
        """
journals:
  - name: Endoscopy
    abbrev: Endoscopy
    if_2025: 11.8
  - name: Endoscopy International Open
    abbrev: Endosc Int Open
    if_2025: "2.3*"
""",
        encoding="utf-8",
    )
    catalog = load_journal_catalog(tmp_path)
    assert catalog is not None
    assert catalog[1].if_2025 == 2.3
    assert catalog[1].if_2025_flag == "*"
    papers = [
        _paper("Endoscopy", paper_id="doi:endo"),
        _paper("Diagnostics", paper_id="doi:diag"),
        _paper("Endoscopy International Open", paper_id="doi:eio"),
    ]
    kept = filter_listed_papers(papers, catalog)
    assert [p.id for p in kept] == ["doi:endo", "doi:eio"]
    assert filter_listed_papers(papers, None) == papers


def test_rss_includes_impact_factor():
    paper = _paper("Endoscopy")
    paper.journal.published = "2026-07-13"
    catalog = [ListedJournal(name="Endoscopy", if_2025=11.8)]
    xml = build_rss(
        [paper],
        feed_title="T",
        feed_link="https://example.com/f",
        feed_description="d",
        journal_catalog=catalog,
    )
    assert "IF 2025 11.8" in xml
    assert "Diagnostics" not in xml
