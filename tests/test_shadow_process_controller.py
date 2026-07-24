import json
from pathlib import Path

from engine.shadow_process_controller import ShadowProcessController


class _FakeProcess:
    pid = 43210


def test_start_records_detached_shadow_command_without_resetting_state(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "live_paper.py").write_text("# worker", encoding="utf-8")
    state = project / "logs" / "live_demo_shadow"
    state.mkdir(parents=True)
    existing = state / "runtime_state.json"
    existing.write_text('{"keep": true}', encoding="utf-8")
    controller = ShadowProcessController(project, "logs/live_demo_shadow")
    monkeypatch.setattr(controller, "_process_command", lambda pid: "" if pid != 43210 else f"python {controller.script} --mode shadow --groups core --loop")
    captured = {}

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return _FakeProcess()

    monkeypatch.setattr("engine.shadow_process_controller.subprocess.Popen", fake_popen)
    status = controller.start(groups="core", interval_seconds=300)
    metadata = json.loads(controller.metadata_file.read_text(encoding="utf-8"))
    assert status.running is True
    assert metadata["pid"] == 43210
    assert "--mode" in captured["command"] and "shadow" in captured["command"]
    assert existing.read_text(encoding="utf-8") == '{"keep": true}'


def test_status_rejects_pid_whose_command_is_not_shadow_worker(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "live_paper.py").write_text("# worker", encoding="utf-8")
    controller = ShadowProcessController(project, "state")
    controller.state_root.mkdir()
    controller.metadata_file.write_text('{"pid": 99}', encoding="utf-8")
    monkeypatch.setattr(controller, "_process_command", lambda _pid: "python unrelated.py")
    assert controller.status().running is False


def test_status_recovers_running_worker_from_runtime_lock(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "live_paper.py").write_text("# worker", encoding="utf-8")
    controller = ShadowProcessController(project, "state")
    controller.state_root.mkdir()
    controller.metadata_file.write_text('{"pid": 111, "groups": "core", "interval_seconds": 300}', encoding="utf-8")
    controller.runtime_lock.write_text('{"pid": 222}', encoding="utf-8")
    monkeypatch.setattr(
        controller,
        "_process_command",
        lambda pid: f"python {controller.script} --mode shadow --loop" if pid == 222 else "",
    )

    status = controller.status()

    assert status.running is True
    assert status.pid == 222


def test_start_removes_only_stale_runtime_lock(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "live_paper.py").write_text("# worker", encoding="utf-8")
    controller = ShadowProcessController(project, "state")
    controller.state_root.mkdir()
    controller.runtime_lock.write_text('{"pid": 123}', encoding="utf-8")
    monkeypatch.setattr(
        controller,
        "_process_command",
        lambda pid: f"python {controller.script} --mode shadow --loop" if pid == 43210 else "",
    )
    monkeypatch.setattr("engine.shadow_process_controller.subprocess.Popen", lambda *_args, **_kwargs: _FakeProcess())

    status = controller.start()

    assert status.running is True
    assert not controller.runtime_lock.exists()


def test_stop_cleans_lock_after_worker_is_gone(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "live_paper.py").write_text("# worker", encoding="utf-8")
    controller = ShadowProcessController(project, "state")
    controller.state_root.mkdir()
    controller.metadata_file.write_text(
        '{"pid": 123, "groups": "core", "interval_seconds": 300}',
        encoding="utf-8",
    )
    controller.runtime_lock.write_text('{"pid": 123}', encoding="utf-8")
    monkeypatch.setattr(controller, "_process_command", lambda _pid: "")

    status = controller.stop()

    assert status.running is False
    assert not controller.runtime_lock.exists()
