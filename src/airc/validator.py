"""Core validation logic for the release-checklist package."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import re

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

ALLOWED_ENVIRONMENTS = {"development", "dev", "test", "staging", "production", "sandbox"}
ALLOWED_INDUSTRIES = {"general", "healthcare", "finance", "insurance", "government"}
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9._-]+)?$")

EXPECTED_MAPPING_PATHS = {
    "metadata",
    "model_validation",
    "model_validation.performance",
    "model_validation.fairness",
    "governance",
    "governance.documentation",
    "governance.approvals",
    "governance.regulatory",
    "infrastructure",
    "infrastructure.testing",
    "infrastructure.monitoring",
    "infrastructure.rollback",
    "incident_readiness",
}

BOOLEAN_GATE_PATHS = {
    "model_validation.performance.bias_evaluation_complete",
    "model_validation.performance.adversarial_testing_complete",
    "model_validation.fairness.subgroup_performance_review",
    "governance.documentation.model_card_complete",
    "governance.documentation.risk_assessment_complete",
    "governance.documentation.explainability_report_complete",
    "governance.approvals.technical_review",
    "governance.approvals.ai_governance_review",
    "governance.approvals.legal_review",
    "governance.approvals.security_review",
    "governance.regulatory.hipaa_assessment_complete",
    "governance.regulatory.sr_11_7_compliance",
    "infrastructure.testing.unit_tests_passing",
    "infrastructure.testing.integration_tests_passing",
    "infrastructure.testing.security_scan_passed",
    "infrastructure.testing.load_test_passed",
    "infrastructure.monitoring.alerting_configured",
    "infrastructure.monitoring.drift_detection_enabled",
    "infrastructure.rollback.rollback_plan_documented",
    "infrastructure.rollback.rollback_tested",
    "incident_readiness.runbook_complete",
    "incident_readiness.escalation_contacts_defined",
}

NUMERIC_BOUNDED_RULES: dict[str, tuple[float, float]] = {
    "model_validation.performance.accuracy_threshold": (0.0, 1.0),
    "model_validation.performance.precision_threshold": (0.0, 1.0),
    "model_validation.performance.recall_threshold": (0.0, 1.0),
    "model_validation.performance.f1_threshold": (0.0, 1.0),
    "model_validation.fairness.disparate_impact_ratio": (0.0, 10.0),
}

POSITIVE_NUMERIC_PATHS = {
    "infrastructure.monitoring.latency_ms",
    "infrastructure.monitoring.timeout_seconds",
    "infrastructure.monitoring.retention_days",
    "infrastructure.monitoring.throughput_rps",
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


def _ensure_string(value: Any, field_name: str) -> str:
    """Validate that a metadata field is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ChecklistValidationError(f"metadata.{field_name} must be a non-empty string")
    return value.strip()


def _ensure_semver(value: str) -> None:
    """Validate a loose semver-like version string."""
    if not SEMVER_PATTERN.match(value):
        raise ChecklistValidationError(
            "metadata.version must look like a semantic version such as 1.0.0"
        )


def _ensure_allowed(value: str, field_name: str, allowed: set[str]) -> str:
    """Validate a normalized metadata field against an allow-list."""
    normalized = value.lower()
    if normalized not in allowed:
        expected = ", ".join(sorted(allowed))
        raise ChecklistValidationError(
            f"metadata.{field_name} must be one of: {expected}"
        )
    return normalized


def _validate_mapping_shapes(config: dict[str, Any]) -> None:
    """Validate that known structural paths are mappings when present."""
    for path in sorted(EXPECTED_MAPPING_PATHS):
        value = _get_nested(config, path)
        if value is None:
            continue
        if not isinstance(value, dict):
            raise ChecklistValidationError(f"{path} must be a mapping/object")


def _validate_leaf_value(path: str, value: Any) -> None:
    """Validate known leaf paths when they are present in the YAML."""
    if path in BOOLEAN_GATE_PATHS and not isinstance(value, bool):
        raise ChecklistValidationError(f"{path} must be a boolean")

    bounds = NUMERIC_BOUNDED_RULES.get(path)
    if bounds is not None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ChecklistValidationError(f"{path} must be a number")
        low, high = bounds
        if not low <= float(value) <= high:
            raise ChecklistValidationError(f"{path} must be between {low} and {high}")

    if path in POSITIVE_NUMERIC_PATHS:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ChecklistValidationError(f"{path} must be a number")
        if float(value) <= 0:
            raise ChecklistValidationError(f"{path} must be greater than 0")

    if path.endswith("_threshold") and isinstance(value, str):
        raise ChecklistValidationError(f"{path} must be numeric, not free-form text")


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

    _validate_mapping_shapes(config)

    metadata = config.get("metadata", {})
    missing_metadata = [field for field in REQUIRED_METADATA if field not in metadata]
    if missing_metadata:
        raise ChecklistValidationError(
            f"Missing required metadata fields: {', '.join(missing_metadata)}"
        )

    project = _ensure_string(metadata.get("project"), "project")
    version = _ensure_string(metadata.get("version"), "version")
    _ensure_semver(version)
    environment = _ensure_allowed(
        _ensure_string(metadata.get("environment"), "environment"),
        "environment",
        ALLOWED_ENVIRONMENTS,
    )
    regulated_industry = _ensure_allowed(
        _ensure_string(metadata.get("regulated_industry"), "regulated_industry"),
        "regulated_industry",
        ALLOWED_INDUSTRIES,
    )
    risk = _ensure_allowed(
        _ensure_string(metadata.get("risk_classification"), "risk_classification"),
        "risk_classification",
        set(REQUIRED_GATES_BY_RISK),
    )

    collected_paths: set[str] = set()
    for section_name in REQUIRED_SECTIONS + ["incident_readiness"]:
        section_value = config.get(section_name)
        if isinstance(section_value, dict):
            section_paths = _collect_paths(section_value, section_name)
            collected_paths.update(section_paths)
            for path in section_paths:
                _validate_leaf_value(path, _get_nested(config, path))

    industry = regulated_industry
    if industry_override is not None:
        industry = _ensure_allowed(industry_override.strip(), "regulated_industry", ALLOWED_INDUSTRIES)

    result = ValidationResult(
        project=project,
        version=version,
        environment=environment,
        risk_classification=risk,
        regulated_industry=industry,
        strict=strict,
    )

    required_gates = set(REQUIRED_GATES_BY_RISK[risk])
    required_gates.update(INDUSTRY_EXTRA_GATES.get(industry, []))

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
