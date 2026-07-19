from pathlib import Path


def workflow_text() -> str:
    return Path(".github/workflows/freakto-forward-test.yml").read_text(encoding="utf-8")


def test_legacy_forward_collector_is_manual_only_and_silent_by_default():
    text = workflow_text()
    trigger_block = text.split("permissions:", 1)[0]
    assert "workflow_dispatch:" in trigger_block
    assert "schedule:" not in trigger_block
    assert 'send_telegram:' in trigger_block
    assert 'default: "false"' in trigger_block


def test_telegram_requires_explicit_manual_opt_in():
    text = workflow_text()
    assert "if: ${{ inputs.send_telegram == 'true' }}" in text
    assert "if: ${{ inputs.send_telegram == 'false' }}" in text
