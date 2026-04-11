"""Core validation logic for the release-checklist package."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ChecklistValidationError(Exception):
    """Raised when the configuration file itself is invalid."""


REQUIRED_SECTIONS = ["metadata", "model_validation", "governance", "infrastructure"]

REQUIRED_METADATA = [
    "project",
    "version",
    "environment",
    "regulated_industry",
    "risk_classification",
]

REQUIRED_GATES_BY_RISK = {
    "high": [
        "model_validation.performance.bias_evaluation_complete",
        "governance.approvals.technical_review",
        "governance.approvals.ai_governance_review",
        "governance.approvals.legal_review",
        "governance.documentation.model_card_complete",
        "governance.documentation.risk_assessment_complete",
        "infrastructure.testing.unit_tests_passing",
        "infrastructure.testing.security_scan_passed",
        "infrastructure.rollback.rollback_plan_documented",
        "incident_readiness.runbook_complete",
    ],
    "medium": [
        "model_validation.performance.bias_evaluation_complete",
        "governance.approvals.technical_review",
        "governance.documentation.risk_assessment_complete",
        "infrastructure.testing.unit_tests_passing",
        "infrastructure.rollback.rollback_plan_documented",
    ],
    "low": [
        "governance.approvals.technical_review",
        "infrastructure.testing.unit_tests_passing",
    ],
}

INDUSTRY_EXTRA_GATES = {
    "healthcare": ["governance.regulatory.hipaa_assessment_complete"],
    "finance": ["governance.regulatory.sr_11_7_compliance"],
    "insurance": ["governance.regulatory.sr_11_7_compliance"],
    "government": ["governance.approvals.legal_review"],
}


def _get_nested(d: dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Traverse a nested mapping using a dot-separated key path."""
    value: Any = d
    for key in key_path.split("."):
        if not isinstance(value, dict):
            return default
        value = value.get(key, default)
    return value


def _collect_paths(d: dict[str, Any], prefix: str = "") -> list[str]:
    """Collect leaf paths from a nested mapping."""
    paths: list[str] = []
    for key, value in d.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            paths.extend(_collect_paths(value, path))
        else:
            paths.append(path)
    return paths


def _is_gate_satisfied(value: Any) -> bool:
    """Return whether a gate value should be treated as satisfied."""
    if isinstance(value, bool):
        return value is True
    return value not in (None, "")


@dataclass
class GateResult:
    gate: str
    value: Any
    passed: bool
    required: bool


@dataclass
class ValidationResult:
    project: str
    version: str
    environment: str
    risk_classification: str
    regulated_industry: str
    strict: bool = False
    gates: list[GateResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        scope = self.gates if self.strict else [gate for gate in self.gates if gate.required]
        return all(gate.passed for gate in scope)

    @property
    def failed_count(self) -> int:
        scope = self.gates if self.strict else [gate for gate in self.gates if gate.required]
        return sum(1 for gate in scope if not gate.passed)

    @property
    def passed_count(self) -> int:
        scope = self.gates if self.strict else [gate for gate in self.gates if gate.required]
        return sum(1 for gate in scope if gate.passed)

    @property
    def total_gates(self) -> int:
        scope = self.gates if self.strict else [gate for gate in self.gates if gate.required]
        return len(scope)


def validate_checklist(
    config_path: Path,
    strict: bool = False,
    industry_override: str | None = None,
) -> ValidationResult:
    """Validate a release checklist YAML configuration file."""
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ChecklistValidationError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(config, dict):
        raise ChecklistValidationError(
            f"{config_path} does not contain a YAML mapping at the top level."
        )

    missing_sections = [section for section in REQUIRED_SECTIONS if section not in config]
    if missing_sections:
        raise ChecklistValidationError(
            f"Missing required sections: {', '.join(missing_sections)}"
        )

    metadata = config.get("metadata", {})
    missing_metadata = [field for field in REQUIRED_METADATA if not metadata.get(field)]
    if missing_metadata:
        raise ChecklistValidationError(
            f"Missing required metadata fields: {', '.join(missing_metadata)}"
        )

    risk = str(metadata["risk_classification"]).lower()
    if risk not in REQUIRED_GATES_BY_RISK:
        allowed = ", ".join(sorted(REQUIRED_GATES_BY_RISK))
        raise ChecklistValidationError(
            f"Unsupported risk_classification '{metadata['risk_classification']}'. "
            f"Expected one of: {allowed}"
        )

    industry = str(industry_override or metadata["regulated_industry"]).lower()

    result = ValidationResult(
        project=str(metadata["project"]),
        version=str(metadata["version"]),
        environment=str(metadata["environment"]),
        risk_classification=risk,
        regulated_industry=industry,
        strict=strict,
    )

    required_gates = set(REQUIRED_GATES_BY_RISK[risk])
    required_gates.update(INDUSTRY_EXTRA_GATES.get(industry, []))

    collected_paths: set[str] = set()
    for section_name in REQUIRED_SECTIONS + ["incident_readiness"]:
        section_value = config.get(section_name)
        if isinstance(section_value, dict):
            collected_paths.update(_collect_paths(section_value, section_name))

    gate_paths = sorted(collected_paths | required_gates)

    for gate_path in gate_paths:
        value = _get_nested(config, gate_path)
        is_required = gate_path in required_gates
        passed = _is_gate_satisfied(value)
        result.gates.append(
            GateResult(
                gate=gate_path,
                value=value,
                passed=passed,
                required=is_required,
            )
        )

    return result
