from pathlib import Path


WORKFLOW = Path(".github/workflows/freakto-paper-cloud.yml")


def _persist_step_source() -> str:
    source = WORKFLOW.read_text(encoding="utf-8")
    marker = "- name: Persist state to paper-state branch"
    assert marker in source
    return source.split(marker, 1)[1]


def test_branch_is_ready_before_state_files_are_copied() -> None:
    step = _persist_step_source()

    checkout_index = step.index("git checkout -B paper-state FETCH_HEAD")
    archive_copy_index = step.index(
        'cp "$ARCHIVE_SOURCE" ./cloud_state.tar.gz'
    )
    manifest_copy_index = step.index(
        'cp "$MANIFEST_SOURCE" ./cloud_state_manifest.json'
    )

    assert checkout_index < archive_copy_index
    assert checkout_index < manifest_copy_index


def test_state_sources_remain_outside_temporary_git_worktree() -> None:
    step = _persist_step_source()

    assert 'SOURCE_STATE_DIR="${GITHUB_WORKSPACE}/.cloud-state"' in step
    assert 'ARCHIVE_SOURCE="${SOURCE_STATE_DIR}/cloud_state.tar.gz"' in step
    assert 'MANIFEST_SOURCE="${SOURCE_STATE_DIR}/cloud_state_manifest.json"' in step
    assert 'cp .cloud-state/cloud_state.tar.gz "$STATE_DIR/"' not in step


def test_persistence_is_no_change_safe() -> None:
    step = _persist_step_source()

    assert "git diff --cached --quiet" in step
    assert "Cloud state unchanged; nothing to persist." in step
    assert "exit 0" in step


def test_push_conflicts_are_retried_from_latest_remote_state() -> None:
    step = _persist_step_source()

    assert "MAX_PUSH_ATTEMPTS=3" in step
    assert 'for attempt in $(seq 1 "$MAX_PUSH_ATTEMPTS")' in step
    assert "git fetch --depth=1 origin paper-state" in step
    assert "rebuilding from latest remote state" in step
    assert "sleep $((attempt * 3))" in step


def test_persistence_never_force_pushes() -> None:
    step = _persist_step_source()

    assert "--force" not in step
    assert "--force-with-lease" not in step
    assert "git push origin HEAD:paper-state" in step


def test_artifact_upload_precedes_state_persistence() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert source.index("- name: Upload cycle reports") < source.index(
        "- name: Persist state to paper-state branch"
    )
