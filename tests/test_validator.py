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


def test_required_section_must_be_mapping(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["governance"] = []
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError, match="governance must be a mapping/object"):
        validate_checklist(path)


def test_nested_section_must_be_mapping(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["model_validation"]["performance"] = []
    path = config_file(bad)
    with pytest.raises(
        ChecklistValidationError,
        match="model_validation.performance must be a mapping/object",
    ):
        validate_checklist(path)


def test_missing_required_metadata_raises(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    del bad["metadata"]["project"]
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_invalid_environment_raises(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["metadata"]["environment"] = "prod"
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_development_environment_is_allowed(config_file):
    good = deepcopy(MINIMAL_CONFIG)
    good["metadata"]["environment"] = "development"
    path = config_file(good)
    result = validate_checklist(path)
    assert result.environment == "development"


def test_invalid_regulated_industry_raises(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["metadata"]["regulated_industry"] = "automotive"
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_invalid_version_format_raises(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["metadata"]["version"] = "v1"
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_unsupported_risk_classification_raises(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["metadata"]["risk_classification"] = "critical"
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_accuracy_threshold_out_of_range_raises(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["model_validation"]["performance"]["accuracy_threshold"] = 1.2
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_threshold_cannot_be_free_form_text(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["model_validation"]["performance"]["accuracy_threshold"] = "high"
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_boolean_gate_type_is_enforced(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["governance"]["approvals"]["technical_review"] = "yes"
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_positive_numeric_monitoring_field_is_enforced(config_file):
    bad = deepcopy(MINIMAL_CONFIG)
    bad["infrastructure"]["monitoring"] = {"latency_ms": 0}
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
