from pathlib import Path

import pytest

from cloud_state_sync import create_state_archive, restore_state_archive


def test_pack_and_restore_selected_state(tmp_path: Path):
    root = tmp_path / "root"
    (root / "logs/paper_cycle").mkdir(parents=True)
    (root / "logs/paper_cycle/last_cycle.json").write_text('{"ok": true}', encoding="utf-8")
    archive = tmp_path / "state.tar.gz"
    manifest = tmp_path / "manifest.json"

    result = create_state_archive(root, archive, manifest)
    assert result["file_count"] == 1

    restored = tmp_path / "restored"
    restore = restore_state_archive(restored, archive)
    assert restore["restored_files"] == 1
    assert (restored / "logs/paper_cycle/last_cycle.json").exists()


def test_restore_rejects_traversal_archive(tmp_path: Path):
    import io
    import tarfile

    archive = tmp_path / "bad.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("../escape.txt")
        payload = b"bad"
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))

    with pytest.raises(ValueError):
        restore_state_archive(tmp_path / "restore", archive)
