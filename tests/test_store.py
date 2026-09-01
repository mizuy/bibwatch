"""Tests for paper ID and storage."""

from bibwatch.store import normalize_doi, paper_id_from_ids


def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.1038/nature12345") == "10.1038/nature12345"
    assert normalize_doi("10.1038/nature12345") == "10.1038/nature12345"


def test_paper_id_priority():
    assert paper_id_from_ids(doi="10.1038/x", pmid="123") == "doi:10.1038/x"
    assert paper_id_from_ids(pmid="123", arxiv="2301.00001") == "pmid:123"
    assert paper_id_from_ids(arxiv="2301.00001", title="Foo") == "arxiv:2301.00001"
