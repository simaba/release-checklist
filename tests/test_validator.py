"""Tests for airc validator module."""
import pytest
import yaml
from pathlib import Path
from airc.validator import validate_checklist, ChecklistValidationError


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


@pytest.fixture
def config_file(tmp_path):
    def _write(config_dict):
        p = tmp_path / "checklist.yaml"
        p.write_text(yaml.dump(config_dict))
        return p
    return _write


def test_minimal_low_risk_config_passes(config_file):
    path = config_file(MINIMAL_CONFIG)
    result = validate_checklist(path)
    assert result.passed


def test_missing_required_section_raises(config_file):
    bad = {k: v for k, v in MINIMAL_CONFIG.items() if k != "governance"}
    path = config_file(bad)
    with pytest.raises(ChecklistValidationError):
        validate_checklist(path)


def test_failed_required_gate_fails(config_file):
    config = {**MINIMAL_CONFIG, "metadata": {**MINIMAL_CONFIG["metadata"], "risk_classification": "medium"}}
    config["governance"]["documentation"] = {"risk_assessment_complete": False}
    path = config_file(config)
    result = validate_checklist(path)
    assert not result.passed
    assert result.failed_count > 0


def test_result_metadata_populated(config_file):
    path = config_file(MINIMAL_CONFIG)
    result = validate_checklist(path)
    assert result.project == "test-project"
    assert result.version == "1.0.0"
    assert result.environment == "staging"
    assert result.risk_classification == "low"
    assert result.regulated_industry == "general"


def test_invalid_yaml_raises(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("{invalid: yaml: content: [}")
    with pytest.raises(ChecklistValidationError):
        validate_checklist(p)


def test_industry_override(config_file):
    config = {**MINIMAL_CONFIG}
    path = config_file(config)
    result = validate_checklist(path, industry_override="healthcare")
    assert result.regulated_industry == "healthcare"
