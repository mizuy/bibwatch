from types import SimpleNamespace

from bibwatch.poll import parse_feed_entry


def test_pubmed_prefers_content_encoded_abstract_and_doi():
    html = (
        '<p style="color: #4aa564;">Best Pract Res Clin Gastroenterol. 2026 Jun;82:102119. '
        "doi: 10.1016/j.bpg.2026.102119. Epub 2026 Jun 11.</p>"
        "<p><b>ABSTRACT</b></p>"
        "<p>BACKGROUND AND AIMS: Advanced rectal lesions need careful optical assessment.</p>"
        "<p>CONCLUSIONS: Organ-preserving algorithms are preferred.</p>"
    )
    entry = SimpleNamespace(
        title="Advanced rectal lesions",
        link="https://pubmed.ncbi.nlm.nih.gov/42642176/",
        summary="CONCLUSIONS: Organ-preserving algorithms are preferred.",
        description="CONCLUSIONS: Organ-preserving algorithms are preferred.",
        content=[{"type": "text/html", "value": html}],
        published="2026-06-11",
        id="https://pubmed.ncbi.nlm.nih.gov/42642176/",
    )
    paper = parse_feed_entry(entry, "w-test", {"type": "pubmed_rss"})
    assert paper.ids["pmid"] == "42642176"
    assert paper.ids["doi"] == "10.1016/j.bpg.2026.102119"
    assert paper.urls["doi"] == "https://doi.org/10.1016/j.bpg.2026.102119"
    assert paper.id.startswith("doi:")
    assert "BACKGROUND AND AIMS" in (paper.abstract.original or "")
    assert (paper.abstract.original or "").startswith("BACKGROUND")


def test_pubmed_falls_back_to_description():
    entry = SimpleNamespace(
        title="A short note",
        link="https://pubmed.ncbi.nlm.nih.gov/111/",
        summary="We report a case.",
        content=[],
        published="2026-01-01",
        id="pmid:111",
    )
    paper = parse_feed_entry(entry, "w-test", {"type": "pubmed"})
    assert paper.ids["pmid"] == "111"
    assert paper.abstract.original == "We report a case."
