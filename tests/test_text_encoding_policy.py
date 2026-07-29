from scripts.validate_text_encoding import main, validate_file


def test_invalid_utf8_and_bom_are_rejected(tmp_path):
    invalid = tmp_path / "invalid.md"
    invalid.write_bytes(b"\xff")
    assert "invalid UTF-8" in validate_file(invalid)[0]
    bom = tmp_path / "bom.py"
    bom.write_bytes(b"\xef\xbb\xbfprint('ok')\n")
    assert any("BOM" in failure for failure in validate_file(bom))


def test_common_mojibake_is_rejected(tmp_path):
    path = tmp_path / "broken.md"
    path.write_text("\u00d8\u00b3\u00d9\u201e\u00d8\u00a7\u00d9\u2026", encoding="utf-8")
    assert any("mojibake" in failure for failure in validate_file(path))


def test_clean_utf8_repository_fixture_passes(tmp_path):
    (tmp_path / "README.md").write_text("سلام — Freakto\n", encoding="utf-8")
    (tmp_path / "module.py").write_text("value = '✅'\n", encoding="utf-8")
    assert main(["--root", str(tmp_path)]) == 0
