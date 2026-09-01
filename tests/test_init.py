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
    result = run_all(tmp_path, site_base="https://example.github.io/data")
    assert result.new_count == 0
    assert result.feed_path is not None
    assert result.feed_path.name == "all.xml"

    issues = run_doctor(tmp_path)
    assert issues == []
