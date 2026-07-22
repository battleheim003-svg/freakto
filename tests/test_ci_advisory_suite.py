from scripts.ci_advisory_suite import profile_commands


def test_forward_profile_runs_collectors_without_health_dry_run_flags():
    commands = dict(profile_commands("forward"))
    assert "--dry-run" not in commands["forward-regime-label"]
    assert "--no-fetch" not in commands["automatic-events"]


def test_health_profile_never_fetches_events_and_uses_label_dry_run():
    commands = dict(profile_commands("health"))
    assert "--dry-run" in commands["forward-regime-label"]
    assert "--no-fetch" in commands["automatic-events"]


def test_each_profile_has_unique_visible_component_names():
    for profile in ("forward", "health"):
        names = [name for name, _ in profile_commands(profile)]
        assert len(names) == len(set(names)) == 14
