"""Validation logic for scoped, evidence-based AI release decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

import yaml


class ChecklistValidationError(Exception):
    """Raised when the configuration itself is structurally incoherent."""


RISK_LEVELS = {"low", "medium", "high"}
OUTCOMES = {"release", "release_with_conditions", "hold", "do_not_release", "defer"}
GATE_STATUSES = {"pass", "fail", "partial", "not_tested", "not_applicable"}
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
PLACEHOLDER_PATTERN = re.compile(r"(?:\[?TBD\]?|YOUR_|REPLACE_|<[^>]+>)", re.IGNORECASE)


@dataclass
class GateResult:
    """One declared proposition and its current evidence status."""

    gate: str
    value: str
    passed: bool
    required: bool
    question: str = ""
    evidence: List[str] = field(default_factory=list)
    owner: str = ""
    limitation: str = ""


@dataclass
class ValidationResult:
    """A validated decision record and its bounded release outcome."""

    project: str
    version: str
    environment: str
    risk_classification: str
    regulated_industry: str
    strict: bool = False
    gates: List[GateResult] = field(default_factory=list)
    outcome: str = "unknown"
    decision_scope: str = ""
    decision_owner: str = ""
    evidence_cutoff: str = ""
    rationale: str = ""
    blockers: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    evidence_gaps: List[str] = field(default_factory=list)
    residual_risks: List[str] = field(default_factory=list)

    @property
    def domain_context(self) -> str:
        """Preferred name for the legacy ``regulated_industry`` field."""
        return self.regulated_industry

    def _scope(self) -> List[GateResult]:
        if self.strict:
            return self.gates
        return [gate for gate in self.gates if gate.required]

    @property
    def passed(self) -> bool:
        return (
            self.outcome in {"release", "release_with_conditions"}
            and not self.blockers
            and all(gate.passed for gate in self._scope())
        )

    @property
    def configuration_valid(self) -> bool:
        """Structural errors raise before a result is returned."""
        return True

    @property
    def failed_count(self) -> int:
        return len(self.blockers) + sum(1 for gate in self._scope() if not gate.passed)

    @property
    def passed_count(self) -> int:
        return sum(1 for gate in self._scope() if gate.passed)

    @property
    def total_gates(self) -> int:
        return len(self._scope())


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _ensure_text(value: Any, path: str) -> str:
    if not _is_nonempty_text(value):
        raise ChecklistValidationError(f"{path} must be a non-empty string")
    return str(value).strip()


def _ensure_list(mapping: Dict[str, Any], key: str) -> List[str]:
    value = mapping.get(key, [])
    if not isinstance(value, list):
        raise ChecklistValidationError(f"decision.{key} must be a list")
    if any(not _is_nonempty_text(item) for item in value):
        raise ChecklistValidationError(f"decision.{key} entries must be non-empty strings")
    return [str(item).strip() for item in value]


def _ensure_iso_date(value: str, path: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ChecklistValidationError(
            f"{path} must be a valid ISO date in YYYY-MM-DD form"
        ) from exc
    return value


def _placeholder_paths(value: Any, path: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            paths.extend(_placeholder_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_placeholder_paths(child, f"{path}[{index}]"))
    elif _is_nonempty_text(value) and PLACEHOLDER_PATTERN.search(str(value)):
        paths.append(path or "<root>")
    return paths


def _load_config(config_path: Path) -> Dict[str, Any]:
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ChecklistValidationError(f"Could not read {config_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ChecklistValidationError(f"Invalid YAML in {config_path}: {exc}") from exc
    if not isinstance(config, dict):
        raise ChecklistValidationError(
            f"{config_path} does not contain a YAML mapping at the top level"
        )
    return config


def _validate_metadata(
    metadata: Any,
    domain_override: Optional[str],
) -> tuple[str, str, str, str, str, str, str]:
    if not isinstance(metadata, dict):
        raise ChecklistValidationError("metadata must be a mapping/object")

    project = _ensure_text(metadata.get("project"), "metadata.project")
    version = _ensure_text(metadata.get("version"), "metadata.version")
    if not SEMVER_PATTERN.fullmatch(version):
        raise ChecklistValidationError(
            "metadata.version must use semantic version form such as 1.2.3 or 1.2.3-pilot"
        )
    environment = _ensure_text(metadata.get("environment"), "metadata.environment")
    risk = _ensure_text(
        metadata.get("risk_classification"),
        "metadata.risk_classification",
    ).lower()
    if risk not in RISK_LEVELS:
        raise ChecklistValidationError(
            "metadata.risk_classification must be one of: "
            + ", ".join(sorted(RISK_LEVELS))
        )

    decision_scope = _ensure_text(
        metadata.get("decision_scope"),
        "metadata.decision_scope",
    )
    decision_owner = _ensure_text(
        metadata.get("decision_owner"),
        "metadata.decision_owner",
    )
    evidence_cutoff = _ensure_iso_date(
        _ensure_text(metadata.get("evidence_cutoff"), "metadata.evidence_cutoff"),
        "metadata.evidence_cutoff",
    )

    declared_domain = metadata.get("domain_context", metadata.get("regulated_industry", "general"))
    domain_context = _ensure_text(
        domain_override if domain_override is not None else declared_domain,
        "metadata.domain_context",
    ).lower()
    return (
        project,
        version,
        environment,
        risk,
        decision_scope,
        decision_owner,
        evidence_cutoff,
        domain_context,
    )


def _validate_gate(gate: Any, index: int, seen_ids: set[str]) -> GateResult:
    prefix = f"gates[{index}]"
    if not isinstance(gate, dict):
        raise ChecklistValidationError(f"{prefix} must be a mapping/object")

    gate_id = _ensure_text(gate.get("id"), f"{prefix}.id")
    if gate_id in seen_ids:
        raise ChecklistValidationError(f"duplicate gate id: {gate_id}")
    seen_ids.add(gate_id)

    question = _ensure_text(gate.get("question"), f"{prefix}.question")
    hard_gate = gate.get("hard_gate")
    if not isinstance(hard_gate, bool):
        raise ChecklistValidationError(f"{prefix}.hard_gate must be true or false")

    status = _ensure_text(gate.get("status"), f"{prefix}.status").lower()
    if status not in GATE_STATUSES:
        raise ChecklistValidationError(
            f"{prefix}.status must be one of: " + ", ".join(sorted(GATE_STATUSES))
        )

    evidence_raw = gate.get("evidence")
    if not isinstance(evidence_raw, list):
        raise ChecklistValidationError(f"{prefix}.evidence must be a list")
    if any(not _is_nonempty_text(item) for item in evidence_raw):
        raise ChecklistValidationError(f"{prefix}.evidence entries must be non-empty strings")
    evidence = [str(item).strip() for item in evidence_raw]

    owner = _ensure_text(gate.get("owner"), f"{prefix}.owner")
    limitation_raw = gate.get("limitation", "")
    if limitation_raw is not None and not isinstance(limitation_raw, str):
        raise ChecklistValidationError(f"{prefix}.limitation must be text when provided")
    limitation = str(limitation_raw or "").strip()

    if status in {"pass", "not_applicable"} and not evidence:
        raise ChecklistValidationError(f"{prefix} with status {status} must cite evidence")
    if status == "not_applicable" and not limitation:
        raise ChecklistValidationError(
            f"{prefix} with status not_applicable requires a scoped rationale in limitation"
        )

    return GateResult(
        gate=gate_id,
        value=status,
        passed=status in {"pass", "not_applicable"},
        required=hard_gate,
        question=question,
        evidence=evidence,
        owner=owner,
        limitation=limitation,
    )


def validate_checklist(
    config_path: Path,
    strict: bool = False,
    industry_override: Optional[str] = None,
) -> ValidationResult:
    """Validate a scoped release-decision YAML configuration.

    ``industry_override`` is retained as a compatibility alias. It changes only
    descriptive domain context; it never injects regulatory or approval gates.
    """
    config = _load_config(config_path)
    required_sections = ("metadata", "decision", "gates")
    missing = [section for section in required_sections if section not in config]
    if missing:
        raise ChecklistValidationError(
            "Missing required sections: " + ", ".join(missing)
        )

    placeholders = _placeholder_paths(config)
    if placeholders:
        raise ChecklistValidationError(
            "Configuration contains placeholders: " + ", ".join(placeholders)
        )

    (
        project,
        version,
        environment,
        risk,
        decision_scope,
        decision_owner,
        evidence_cutoff,
        domain_context,
    ) = _validate_metadata(config.get("metadata"), industry_override)

    decision = config.get("decision")
    if not isinstance(decision, dict):
        raise ChecklistValidationError("decision must be a mapping/object")
    outcome = _ensure_text(decision.get("outcome"), "decision.outcome").lower()
    if outcome not in OUTCOMES:
        raise ChecklistValidationError(
            "decision.outcome must be one of: " + ", ".join(sorted(OUTCOMES))
        )
    rationale = _ensure_text(decision.get("rationale"), "decision.rationale")
    blockers = _ensure_list(decision, "blockers")
    required_actions = _ensure_list(decision, "required_actions")
    conditions = _ensure_list(decision, "conditions")
    evidence_gaps = _ensure_list(decision, "evidence_gaps")
    residual_risks = _ensure_list(decision, "residual_risks")

    gates_raw = config.get("gates")
    if not isinstance(gates_raw, list):
        raise ChecklistValidationError("gates must be a list")
    if not gates_raw:
        raise ChecklistValidationError("At least one gate is required")
    seen_ids: set[str] = set()
    gates = [_validate_gate(gate, index, seen_ids) for index, gate in enumerate(gates_raw)]

    unresolved_hard = [gate.gate for gate in gates if gate.required and not gate.passed]
    decision_blockers = list(blockers)
    decision_blockers.extend(f"unresolved hard gate: {gate_id}" for gate_id in unresolved_hard)

    if outcome == "release" and (required_actions or conditions):
        raise ChecklistValidationError(
            "release cannot include required_actions or conditions"
        )
    if outcome == "release_with_conditions" and not (required_actions or conditions):
        raise ChecklistValidationError(
            "release_with_conditions requires at least one condition or required action"
        )
    if outcome == "defer" and not evidence_gaps:
        raise ChecklistValidationError("defer requires at least one evidence gap")
    if outcome == "do_not_release" and not decision_blockers:
        raise ChecklistValidationError(
            "do_not_release requires a blocker or unresolved hard gate"
        )

    return ValidationResult(
        project=project,
        version=version,
        environment=environment,
        risk_classification=risk,
        regulated_industry=domain_context,
        strict=strict,
        gates=gates,
        outcome=outcome,
        decision_scope=decision_scope,
        decision_owner=decision_owner,
        evidence_cutoff=evidence_cutoff,
        rationale=rationale,
        blockers=decision_blockers,
        required_actions=required_actions,
        conditions=conditions,
        evidence_gaps=evidence_gaps,
        residual_risks=residual_risks,
    )
