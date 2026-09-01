"""Tests for init and doctor."""

from pathlib import Path

from bibwatch.doctor import run_doctor
from bibwatch.init_data import init_data_root
from bibwatch.run import run_all


def test_init_and_run_empty(tmp_path: Path):
    init_data_root(tmp_path, feed_token="test-token-uuid-12345678")
    issues = run_doctor(tmp_path)
    assert any("feed not found" in i for i in issues)

    (tmp_path / "watches" / "w-test.yaml").write_text(
        "id: w-test\ntitle: Test\nenabled: false\nfeeds: []\n",
        encoding="utf-8",
    )
    feed_repo = tmp_path / "bibwatch-feed"
    result = run_all(
        tmp_path,
        site_base="https://example.github.io/bibwatch-feed",
        feed_root=feed_repo,
    )
    assert result.new_count == 0
    assert result.feed_path is not None
    assert result.feed_path.name == "all.xml"
    public_feed = feed_repo / "docs" / "feeds" / "test-token-uuid-12345678" / "all.xml"
    assert public_feed.is_file()
    assert public_feed.read_text(encoding="utf-8") == result.feed_path.read_text(encoding="utf-8")
    assert (feed_repo / "docs" / "feeds" / "test-token-uuid-12345678" / "priority.xml").is_file()
    assert (feed_repo / "docs" / ".nojekyll").is_file()
    assert "https://example.github.io/bibwatch-feed/feeds/test-token-uuid-12345678/all.xml" in public_feed.read_text(
        encoding="utf-8"
    )

    issues = run_doctor(tmp_path, feed_root=feed_repo)
    assert issues == []
