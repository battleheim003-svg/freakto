from __future__ import annotations

from airdrop.outcomes import (
    OutcomeObservation,
    OutcomeTracker,
    PredictionSnapshot,
    build_backtest_report,
)
from airdrop.outcomes.cli import main


def _prediction(identity: str, score: int, predicted_at: str) -> PredictionSnapshot:
    return PredictionSnapshot(
        identity=identity,
        name=identity,
        predicted_at=predicted_at,
        score=score,
        level="WATCH",
        scored_json="{}",
    )


def test_predictions_are_immutable_and_idempotent(tmp_path):
    tracker = OutcomeTracker(tmp_path / "outcomes.db")
    prediction = _prediction("alpha", 75, "2024-01-01T00:00:00Z")
    assert tracker.record_prediction(prediction)
    assert not tracker.record_prediction(prediction)


def test_outcome_must_follow_prediction_and_have_evidence(tmp_path):
    tracker = OutcomeTracker(tmp_path / "outcomes.db")
    tracker.record_prediction(_prediction("alpha", 75, "2024-01-02T00:00:00Z"))
    observation = OutcomeObservation(
        identity="alpha",
        observed_at="2024-01-01T00:00:00Z",
        status="CLAIMED",
        eligible=True,
        claimed=True,
        source_ref="receipt:1",
    )
    try:
        tracker.record_outcome(observation)
    except ValueError as exc:
        assert "later than" in str(exc)
    else:
        raise AssertionError("Pre-prediction outcome should be blocked.")


def test_pending_is_right_censored_and_not_counted_as_failure(tmp_path):
    tracker = OutcomeTracker(tmp_path / "outcomes.db")
    tracker.record_prediction(_prediction("pending", 80, "2024-01-01T00:00:00Z"))
    tracker.record_prediction(_prediction("winner", 90, "2024-01-01T00:00:00Z"))
    tracker.record_outcome(
        OutcomeObservation(
            identity="pending",
            observed_at="2024-02-01T00:00:00Z",
            status="PENDING",
            eligible=None,
            source_ref="research-note:pending",
        )
    )
    tracker.record_outcome(
        OutcomeObservation(
            identity="winner",
            observed_at="2024-02-01T00:00:00Z",
            status="CLAIMED",
            eligible=True,
            claimed=True,
            gross_reward_usd=100,
            cost_usd=10,
            source_ref="receipt:winner",
        )
    )
    report = build_backtest_report(tracker, min_resolved=2)
    assert report.status == "RESEARCH_CANDIDATE"
    assert report.resolved_projects == 1
    assert report.pending_projects == 1
    assert report.success_rate_pct == 100.0


def test_report_passed_means_sample_complete_not_profit_claim(tmp_path):
    tracker = OutcomeTracker(tmp_path / "outcomes.db")
    for identity, score, reward in (("a", 20, 0), ("b", 90, 20)):
        tracker.record_prediction(_prediction(identity, score, "2024-01-01T00:00:00Z"))
        tracker.record_outcome(
            OutcomeObservation(
                identity=identity,
                observed_at="2024-02-01T00:00:00Z",
                status="CLAIMED" if reward else "NO_AIRDROP",
                eligible=bool(reward),
                claimed=bool(reward),
                gross_reward_usd=reward,
                source_ref=f"evidence:{identity}",
            )
        )
    report = build_backtest_report(tracker, min_resolved=2)
    assert report.status == "PASSED"
    assert report.resolved_projects == 2
    assert any("not profitability" in note for note in report.notes)


def test_sync_missing_source_fails_closed_without_traceback(tmp_path, capsys):
    code = main(
        [
            "--db",
            str(tmp_path / "outcomes.db"),
            "sync",
            "--source-db",
            str(tmp_path / "missing.db"),
        ]
    )
    assert code == 2
    output = capsys.readouterr().out
    assert '"status": "SYNC_BLOCKED"' in output
    assert "AIRDROP_RADAR_DATABASE_NOT_FOUND" in output
