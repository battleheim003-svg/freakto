"""SQLite experiment registry for reproducible research runs.

The registry is intentionally independent from DecisionEngine.  It stores run
identity and provenance, never score logic or calibration behavior.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from engine.model_contract import CURRENT_MODEL_CONTRACT, ModelContract
from engine.research_contracts import LEGACY_EVENT_META_WALK_FORWARD_CONTRACT


DEFAULT_REGISTRY_PATH = Path("logs") / "experiments" / "experiment_registry.sqlite3"
DEFAULT_GOVERNANCE_PATH = Path(__file__).resolve().parents[1] / "config" / "research_experiment_governance.json"
TERMINAL_HOLDOUT_STATUS = "HOLDOUT_CONSUMED_NOT_VALIDATED"
TERMINAL_RESEARCH_OUTCOME = "HOLDOUT_CRITERIA_FAILED"
GOVERNANCE_BLOCKERS = (
    TERMINAL_HOLDOUT_STATUS,
    TERMINAL_RESEARCH_OUTCOME,
    "PROMOTION_NOT_ELIGIBLE",
    "NO_VALID_DEVELOPMENT_CANDIDATE",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GovernedExperiment:
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.payload)

    @property
    def experiment_id(self) -> str:
        return str(self.payload["experiment_id"])

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((*GOVERNANCE_BLOCKERS, *self.payload["failure_reasons"])))


class ResearchGovernanceRegistry:
    """Read-only, version-controlled terminal research governance."""

    def __init__(self, path: str | Path = DEFAULT_GOVERNANCE_PATH):
        self.path = Path(path)
        self._records = self._load()

    def _load(self) -> Dict[str, GovernedExperiment]:
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"GOVERNANCE_REGISTRY_INVALID: {type(exc).__name__}") from exc
        if document.get("schema_version") != "1.0.0":
            raise ValueError("GOVERNANCE_REGISTRY_INVALID: unknown schema version")
        records: Dict[str, GovernedExperiment] = {}
        digests: Dict[str, str] = {}
        for payload in document.get("experiments", []):
            self._validate(payload)
            experiment_id = str(payload["experiment_id"])
            digest = fingerprint(payload)
            if experiment_id in records and digests[experiment_id] != digest:
                raise ValueError(f"GOVERNANCE_RECORD_CONFLICT: {experiment_id}")
            records[experiment_id] = GovernedExperiment(dict(payload))
            digests[experiment_id] = digest
        return records

    @staticmethod
    def _validate(payload: Dict[str, Any]) -> None:
        required = {
            "experiment_id", "code_commit", "artifact_selector", "replay_fingerprint",
            "event_evidence_digest", "split_protocol", "split_profile",
            "walk_forward_contract_version", "walk_forward_folds",
            "experiment_status", "research_outcome", "promotion_eligible",
            "terminal", "development_candidate_selected", "failure_reasons",
            "evidence_roots", "evidence_hashes",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ValueError(f"GOVERNANCE_REGISTRY_INVALID: missing {missing}")
        if payload["experiment_status"] != TERMINAL_HOLDOUT_STATUS:
            raise ValueError("GOVERNANCE_REGISTRY_INVALID: unknown experiment status")
        if payload["research_outcome"] != TERMINAL_RESEARCH_OUTCOME:
            raise ValueError("GOVERNANCE_REGISTRY_INVALID: unknown research outcome")
        if payload["promotion_eligible"] is not False or payload["terminal"] is not True:
            raise ValueError("GOVERNANCE_REGISTRY_INVALID: terminal experiment is not immutable")
        if payload["development_candidate_selected"] is not False:
            raise ValueError("GOVERNANCE_REGISTRY_INVALID: terminal experiment cannot select a candidate")
        if (
            payload["walk_forward_contract_version"] != LEGACY_EVENT_META_WALK_FORWARD_CONTRACT
            or int(payload["walk_forward_folds"]) != 3
        ):
            raise ValueError("GOVERNANCE_REGISTRY_INVALID: Phase 6G legacy contract mismatch")
        for value in (payload["replay_fingerprint"], payload["event_evidence_digest"]):
            if len(str(value)) != 64:
                raise ValueError("GOVERNANCE_REGISTRY_INVALID: evidence fingerprint mismatch")

    def get(self, experiment_id: str) -> GovernedExperiment | None:
        return self._records.get(str(experiment_id))

    def for_selector(self, selector: str) -> GovernedExperiment | None:
        matches = [r for r in self._records.values() if r.payload["artifact_selector"] == selector]
        if len(matches) > 1:
            raise ValueError(f"GOVERNANCE_RECORD_CONFLICT: selector {selector}")
        return matches[0] if matches else None

    def require_promotion_eligible(
        self,
        *,
        experiment_id: str = "",
        artifact_selector: str = "",
        replay_fingerprint: str = "",
    ) -> GovernedExperiment:
        record = self.get(experiment_id) if experiment_id else self.for_selector(artifact_selector)
        if record is None:
            raise ValueError("PROMOTION_NOT_ELIGIBLE: governance record is missing")
        if replay_fingerprint and replay_fingerprint != record.payload["replay_fingerprint"]:
            raise ValueError("PROMOTION_NOT_ELIGIBLE: evidence fingerprint mismatch")
        if record.payload["terminal"] or not record.payload["promotion_eligible"]:
            raise ValueError(" | ".join(record.blockers))
        return record

    def require_contract(self, experiment_id: str, contract_version: str) -> GovernedExperiment:
        record = self.get(experiment_id)
        if record is None:
            raise ValueError("GOVERNANCE_REGISTRY_INVALID: experiment is missing")
        if record.payload["walk_forward_contract_version"] != contract_version:
            raise ValueError("LEGACY_REINTERPRETATION_FORBIDDEN: contract mismatch")
        return record


@dataclass
class ExperimentRun:
    run_id: str
    run_type: str
    status: str
    started_utc: str
    finished_utc: str = ""
    feature_set_version: str = ""
    model_version: str = ""
    calibration_version: str = ""
    execution_model_version: str = ""
    split_protocol_version: str = ""
    data_start_utc: str = ""
    data_end_utc: str = ""
    data_fingerprint: str = ""
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    parent_run_id: str = ""
    notes: str = ""


class ExperimentRegistry:
    def __init__(self, path: str | Path = DEFAULT_REGISTRY_PATH):
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=30)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        self._initialize(connection)
        return connection

    @staticmethod
    def _initialize(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS experiment_runs (
                run_id TEXT PRIMARY KEY,
                run_type TEXT NOT NULL,
                status TEXT NOT NULL,
                started_utc TEXT NOT NULL,
                finished_utc TEXT NOT NULL DEFAULT '',
                feature_set_version TEXT NOT NULL,
                model_version TEXT NOT NULL,
                calibration_version TEXT NOT NULL,
                execution_model_version TEXT NOT NULL,
                split_protocol_version TEXT NOT NULL,
                data_start_utc TEXT NOT NULL DEFAULT '',
                data_end_utc TEXT NOT NULL DEFAULT '',
                data_fingerprint TEXT NOT NULL DEFAULT '',
                hyperparameters_json TEXT NOT NULL,
                results_json TEXT NOT NULL,
                parent_run_id TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_experiment_type_time
                ON experiment_runs(run_type, started_utc);
            CREATE TABLE IF NOT EXISTS holdout_claims (
                dataset_fingerprint TEXT NOT NULL,
                experiment_family TEXT NOT NULL,
                run_id TEXT NOT NULL,
                claimed_utc TEXT NOT NULL,
                PRIMARY KEY(dataset_fingerprint, experiment_family)
            );
            """
        )

    def start_run(
        self,
        run_id: str,
        run_type: str,
        *,
        hyperparameters: Optional[Dict[str, Any]] = None,
        data_start_utc: str = "",
        data_end_utc: str = "",
        data_fingerprint: str = "",
        contract: ModelContract = CURRENT_MODEL_CONTRACT,
        parent_run_id: str = "",
        notes: str = "",
        replace_existing: bool = True,
    ) -> ExperimentRun:
        run = ExperimentRun(
            run_id=run_id,
            run_type=run_type.upper(),
            status="RUNNING",
            started_utc=_utc_now(),
            feature_set_version=contract.feature_set_version,
            model_version=contract.model_version,
            calibration_version=contract.calibration_version,
            execution_model_version=contract.execution_model_version,
            split_protocol_version=contract.split_protocol_version,
            data_start_utc=data_start_utc,
            data_end_utc=data_end_utc,
            data_fingerprint=data_fingerprint,
            hyperparameters=dict(hyperparameters or {}),
            parent_run_id=parent_run_id,
            notes=notes,
        )
        with self._connect() as connection:
            verb = "INSERT OR REPLACE" if replace_existing else "INSERT"
            try:
                connection.execute(
                    f"""{verb} INTO experiment_runs VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run.run_id, run.run_type, run.status, run.started_utc, run.finished_utc,
                        run.feature_set_version, run.model_version, run.calibration_version,
                        run.execution_model_version, run.split_protocol_version,
                        run.data_start_utc, run.data_end_utc, run.data_fingerprint,
                        _canonical_json(run.hyperparameters), _canonical_json(run.results),
                        run.parent_run_id, run.notes,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise FileExistsError(f"experiment run already exists: {run_id}") from exc
        return run

    def finish_run(self, run_id: str, status: str, results: Dict[str, Any]) -> None:
        normalized = status.upper()
        if normalized not in {"COMPLETED", "FAILED", "BLOCKED"}:
            raise ValueError(f"invalid terminal experiment status: {status}")
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE experiment_runs SET status=?, finished_utc=?, results_json=? WHERE run_id=?",
                (normalized, _utc_now(), _canonical_json(results), run_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"experiment run not found: {run_id}")

    def update_data_provenance(
        self, run_id: str, *, data_start_utc: str, data_end_utc: str, data_fingerprint: str
    ) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE experiment_runs
                   SET data_start_utc=?, data_end_utc=?, data_fingerprint=?
                   WHERE run_id=?""",
                (data_start_utc, data_end_utc, data_fingerprint, run_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"experiment run not found: {run_id}")

    def claim_holdout(self, dataset_fingerprint: str, experiment_family: str, run_id: str) -> bool:
        """Atomically claim one final hold-out evaluation.

        Returns False if this dataset/family has already consumed its final
        hold-out.  Callers must then block rather than inspect TEST outcomes.
        """
        if not dataset_fingerprint:
            raise ValueError("dataset_fingerprint is required for a holdout claim")
        with self._connect() as connection:
            try:
                connection.execute(
                    "INSERT INTO holdout_claims VALUES (?, ?, ?, ?)",
                    (dataset_fingerprint, experiment_family, run_id, _utc_now()),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def get_run(self, run_id: str) -> Optional[ExperimentRun]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM experiment_runs WHERE run_id=?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        values = list(row)
        values[13] = json.loads(values[13] or "{}")
        values[14] = json.loads(values[14] or "{}")
        return ExperimentRun(*values)

    def latest_run(self, run_type: str, *, parent_run_id: str = "") -> Optional[ExperimentRun]:
        query = "SELECT run_id FROM experiment_runs WHERE run_type=?"
        parameters: list[str] = [run_type.upper()]
        if parent_run_id:
            query += " AND parent_run_id=?"
            parameters.append(parent_run_id)
        query += " ORDER BY started_utc DESC LIMIT 1"
        with self._connect() as connection:
            row = connection.execute(query, parameters).fetchone()
        return self.get_run(str(row[0])) if row else None

    def set_parent_run(self, run_id: str, parent_run_id: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE experiment_runs SET parent_run_id=? WHERE run_id=?",
                (parent_run_id, run_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"experiment run not found: {run_id}")

    def export_run(self, run_id: str) -> Dict[str, Any]:
        run = self.get_run(run_id)
        return asdict(run) if run else {}
