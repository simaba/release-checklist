"""Tests for the release-checklist validator."""

from __future__ import annotations

from copy import deepcopy

import pytest
import yaml

from airc.validator import ChecklistValidationError, validate_checklist


MINIMAL_CONFIG = {
    "metadata": {
        "project": "test-project",
        "version": "1.0.0",
        "environment": "staging",
        "regulated_industry": "general",
        "risk_classification": "low",
    },
    "model_validation": {
        "performance": {"accuracy_threshold": 0.90, "bias_evaluation_complete": True}
    },
    "governance": {
        "approvals": {"technical_review": True}
    },
    "infrastructure": {
        "testing": {"unit_tests_passing": True}
    },
}


@pytest.fixture()
def config_file(tmp_path):
    def _write(config_dict):
        path = tmp_path / "checklist.yaml"
        path.write_text(yaml.dump(config_dict), encoding="utf-8")
        return path

    return _write


def test_minimal_low_risk_config_passes(config_file):
    path = config_file(MINIMAL_CONFIG)
    result = validate_checklist(path)
    assert result.passed
    assert result.failed_count == 0


def test_missing_required_section_raises(config_file):
    bad = {key: value for key, value in MINIMAL_CONFIG.items() if key != "governance"}
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_missing_required_metadata_raises(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    del bad["metadata"]["project"]
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_unsupported_risk_classification_raises(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["metadata"]["risk_classification"] = "critical"
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_failed_required_gate_fails(config_file):
    config = deepcopy(MINIMAL_CONFIG)
    config["metadata"]["risk_classification"] = "medium"
    config["governance"]["documentation"] = {"risk_assessment_complete": False}
    config["infrastructure"]["rollback"] = {"rollback_plan_documented": True}
    path = config_file(config)
    result = validate_checklist(path)
    assert not result.passed
    assert result.failed_count > 0


def test_missing_required_gate_that_is_not_present_in_yaml_still_fails(config_file):
    config = deepcopy(MINIMAL_CONFIG)
    config["metadata"]["risk_classification"] = "high"
    config["governance"]["approvals"]["ai_governance_review"] = True
    config["governance"]["approvals"]["legal_review"] = True
    config["governance"]["documentation"] = {
        "model_card_complete": True,
        "risk_assessment_complete": True,
    }
    config["infrastructure"]["testing"]["security_scan_passed"] = True
    config["infrastructure"]["rollback"] = {"rollback_plan_documented": True}
    path = config_file(config)
    result = validate_checklist(path)
    assert not result.passed
    failed_required = {gate.gate for gate in result.gates if gate.required and not gate.passed}
    assert "incident_readiness.runbook_complete" in failed_required


def test_result_metadata_populated(config_file):
    path = config_file(MINIMAL_CONFIG)
    result = validate_checklist(path)
    assert result.project == "test-project"
    assert result.version == "1.0.0"
    assert result.environment == "staging"
    assert result.risk_classification == "low"
    assert result.regulated_industry == "general"


def test_invalid_yaml_raises(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("{invalid: yaml: content: [}", encoding="utf-8")
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_industry_override(config_file):
    path = config_file(MINIMAL_CONFIG)
    result = validate_checklist(path, industry_override="healthcare")
    assert result.regulated_industry == "healthcare"


def test_strict_mode_fails_optional_boolean_gates(config_file):
    config = deepcopy(MINIMAL_CONFIG)
    config["model_validation"]["performance"]["bias_evaluation_complete"] = False
    path = config_file(config)

    relaxed = validate_checklist(path, strict=False)
    strict = validate_checklist(path, strict=True)

    assert relaxed.passed
    assert strict.strict is True
    assert not strict.passed
    assert strict.failed_count >= 1
