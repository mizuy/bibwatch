from pathlib import Path

from bibwatch.init_data import init_data_root
from bibwatch.models import Abstract, Journal, Paper
from bibwatch.run import publish_all_feeds
from bibwatch.store import save_paper
from bibwatch.translate import (
    apply_abstract_translation,
    apply_translations_file,
    papers_needing_translation,
    translate_paper_abstract,
)


def _paper(paper_id: str, *, ja: str | None = None) -> Paper:
    return Paper(
        id=paper_id,
        title="A paper",
        journal=Journal(name="Gut", published="2026-08-01"),
        abstract=Abstract(original="We studied serrated lesions.", ja=ja, translated=bool(ja)),
    )


def test_cache_only_no_api(tmp_path: Path):
    init_data_root(tmp_path, feed_token="test-token-uuid-12345678")
    paper = _paper("doi:1")
    out = translate_paper_abstract(tmp_path, paper)
    assert out.abstract.ja is None
    assert out.abstract.translated is False


def test_apply_and_list(tmp_path: Path):
    init_data_root(tmp_path, feed_token="test-token-uuid-12345678")
    save_paper(tmp_path, _paper("doi:need"))
    save_paper(tmp_path, _paper("doi:done", ja="訳済み"))
    pending = papers_needing_translation(tmp_path, in_feeds=False)
    assert [p.id for p in pending] == ["doi:need"]
    apply_abstract_translation(tmp_path, "doi:need", "鋸歯状病変を検討した。")
    again = translate_paper_abstract(tmp_path, _paper("doi:need"))
    assert again.abstract.ja == "鋸歯状病変を検討した。"
    assert papers_needing_translation(tmp_path, in_feeds=False) == []


def test_apply_file_and_publish(tmp_path: Path):
    init_data_root(tmp_path, feed_token="test-token-uuid-12345678")
    (tmp_path / "watches" / "w-test.yaml").write_text(
        "id: w-test\ntitle: Test\nenabled: false\nfeeds: []\n",
        encoding="utf-8",
    )
    save_paper(tmp_path, _paper("doi:need"))
    batch = tmp_path / "batch.yaml"
    batch.write_text(
        "translations:\n  - id: doi:need\n    ja: 日本語要旨\n",
        encoding="utf-8",
    )
    applied = apply_translations_file(tmp_path, batch)
    assert applied == ["doi:need"]
    feed_repo = tmp_path / "bibwatch-feed"
    path, paths = publish_all_feeds(
        tmp_path,
        site_base="https://example.github.io/bibwatch-feed",
        feed_root=feed_repo,
    )
    assert path is not None
    xml = path.read_text(encoding="utf-8")
    assert "日本語要旨" in xml
    assert paths
