from __future__ import annotations

from copy import deepcopy

import yaml

from airc.validator import validate_checklist


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
    "governance": {"approvals": {"technical_review": True}},
    "infrastructure": {"testing": {"unit_tests_passing": True}},
}


def write_config(tmp_path, config):
    path = tmp_path / "checklist.yaml"
    path.write_text(yaml.dump(config), encoding="utf-8")
    return path


def test_strict_mode_ignores_unknown_free_form_fields(tmp_path):
    config = deepcopy(MINIMAL_CONFIG)
    config["governance"]["owner"] = "TBD"
    config["governance"]["notes"] = "Awaiting final meeting"

    result = validate_checklist(write_config(tmp_path, config), strict=True)

    assert result.passed
    assert {gate.gate for gate in result.gates} == {
        "governance.approvals.technical_review",
        "infrastructure.testing.unit_tests_passing",
        "model_validation.performance.bias_evaluation_complete",
    }


def test_explicit_pass_status_satisfies_declared_control(tmp_path):
    config = deepcopy(MINIMAL_CONFIG)
    config["governance"]["approvals"]["technical_review"] = "pass"
    config["infrastructure"]["testing"]["unit_tests_passing"] = "pass"

    result = validate_checklist(write_config(tmp_path, config))

    assert result.passed


def test_pending_status_never_satisfies_required_gate(tmp_path):
    config = deepcopy(MINIMAL_CONFIG)
    config["governance"]["approvals"]["technical_review"] = "evidence_pending"

    result = validate_checklist(write_config(tmp_path, config))

    assert not result.passed
    assert result.failed_count == 1
