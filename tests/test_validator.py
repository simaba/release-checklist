"""Tests for the evidence-based release-checklist validator."""

from __future__ import annotations

from copy import deepcopy

import pytest
import yaml

from airc.validator import ChecklistValidationError, validate_checklist


BASE_CONFIG = {
    "metadata": {
        "project": "Fictional Assistant",
        "version": "1.0.0-pilot",
        "environment": "staging",
        "risk_classification": "medium",
        "domain_context": "library-operations",
        "decision_scope": "20 trained staff; public records; read and draft tools only",
        "decision_owner": "Fictional Sponsor",
        "evidence_cutoff": "2026-10-15",
    },
    "decision": {
        "outcome": "release_with_conditions",
        "rationale": "The fictional evidence supports only a bounded pilot.",
        "blockers": [],
        "required_actions": ["Complete the larger rare-record sample before expansion."],
        "conditions": ["Keep all tools read-only."],
        "evidence_gaps": ["Rare-record coverage remains limited."],
        "residual_risks": ["Users may over-trust fluent drafts."],
    },
    "gates": [
        {
            "id": "AUTH-001",
            "question": "Is write authority disabled for the reviewed scope?",
            "hard_gate": True,
            "status": "pass",
            "evidence": ["evidence/fictional-authority-test.json"],
            "owner": "Fictional Platform Owner",
            "limitation": "Pilot configuration only.",
        },
        {
            "id": "EVAL-001",
            "question": "Does evaluation evidence support the bounded pilot?",
            "hard_gate": False,
            "status": "partial",
            "evidence": ["evidence/fictional-evaluation.md"],
            "owner": "Fictional Evaluation Owner",
            "limitation": "Rare slice remains small.",
        },
    ],
}


@pytest.fixture()
def config_file(tmp_path):
    def _write(config_dict):
        path = tmp_path / "checklist.yaml"
        path.write_text(yaml.safe_dump(config_dict, sort_keys=False), encoding="utf-8")
        return path

    return _write


def test_valid_conditional_release_passes(config_file):
    result = validate_checklist(config_file(BASE_CONFIG))

    assert result.passed is True
    assert result.configuration_valid is True
    assert result.outcome == "release_with_conditions"
    assert result.failed_count == 0
    assert result.domain_context == "library-operations"
    assert result.conditions == ["Keep all tools read-only."]


def test_missing_required_section_raises(config_file):
    bad = deepcopy(BASE_CONFIG)
    del bad["decision"]

    with pytest.raises(ChecklistValidationError, match="Missing required sections: decision"):
        validate_checklist(config_file(bad))


def test_metadata_must_be_mapping(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["metadata"] = []

    with pytest.raises(ChecklistValidationError, match="metadata must be a mapping/object"):
        validate_checklist(config_file(bad))


def test_missing_required_metadata_raises(config_file):
    bad = deepcopy(BASE_CONFIG)
    del bad["metadata"]["decision_owner"]

    with pytest.raises(ChecklistValidationError, match="metadata.decision_owner"):
        validate_checklist(config_file(bad))


def test_invalid_semver_raises(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["metadata"]["version"] = "pilot version one"

    with pytest.raises(ChecklistValidationError, match="semantic version"):
        validate_checklist(config_file(bad))


def test_invalid_evidence_cutoff_raises(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["metadata"]["evidence_cutoff"] = "15 October 2026"

    with pytest.raises(ChecklistValidationError, match="valid ISO date"):
        validate_checklist(config_file(bad))


def test_unsupported_risk_classification_raises(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["metadata"]["risk_classification"] = "critical"

    with pytest.raises(ChecklistValidationError, match="risk_classification"):
        validate_checklist(config_file(bad))


def test_recursive_placeholder_detection_raises(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["decision"]["conditions"][0] = "[TBD: condition]"

    with pytest.raises(
        ChecklistValidationError,
        match=r"decision.conditions\[0\]",
    ):
        validate_checklist(config_file(bad))


def test_duplicate_gate_ids_raise(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["gates"].append(deepcopy(bad["gates"][0]))

    with pytest.raises(ChecklistValidationError, match="duplicate gate id: AUTH-001"):
        validate_checklist(config_file(bad))


def test_pass_gate_requires_evidence(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["gates"][0]["evidence"] = []

    with pytest.raises(ChecklistValidationError, match="status pass must cite evidence"):
        validate_checklist(config_file(bad))


def test_not_applicable_requires_evidence_and_rationale(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["gates"][0]["status"] = "not_applicable"
    bad["gates"][0]["limitation"] = ""

    with pytest.raises(ChecklistValidationError):
        validate_checklist(config_file(bad))


def test_unresolved_hard_gate_blocks_release_result(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["gates"][0]["status"] = "fail"

    result = validate_checklist(config_file(bad))

    assert result.passed is False
    assert "unresolved hard gate: AUTH-001" in result.blockers
    assert result.failed_count >= 2  # one unresolved gate plus its blocker record


def test_release_cannot_hide_conditions(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["decision"]["outcome"] = "release"

    with pytest.raises(
        ChecklistValidationError,
        match="release cannot include required_actions or conditions",
    ):
        validate_checklist(config_file(bad))


def test_conditional_release_requires_condition_or_action(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["decision"]["required_actions"] = []
    bad["decision"]["conditions"] = []

    with pytest.raises(ChecklistValidationError, match="requires at least one"):
        validate_checklist(config_file(bad))


def test_defer_requires_evidence_gap(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["decision"]["outcome"] = "defer"
    bad["decision"]["required_actions"] = []
    bad["decision"]["conditions"] = []
    bad["decision"]["evidence_gaps"] = []

    with pytest.raises(ChecklistValidationError, match="defer requires"):
        validate_checklist(config_file(bad))


def test_do_not_release_requires_reason(config_file):
    bad = deepcopy(BASE_CONFIG)
    bad["decision"]["outcome"] = "do_not_release"
    bad["decision"]["required_actions"] = []
    bad["decision"]["conditions"] = []

    with pytest.raises(ChecklistValidationError, match="requires a blocker"):
        validate_checklist(config_file(bad))


def test_hold_is_valid_but_not_a_supported_release(config_file):
    hold = deepcopy(BASE_CONFIG)
    hold["decision"]["outcome"] = "hold"
    hold["decision"]["blockers"] = ["Known routing failure remains open."]
    hold["gates"][0]["status"] = "fail"

    result = validate_checklist(config_file(hold))

    assert result.configuration_valid is True
    assert result.outcome == "hold"
    assert result.passed is False
    assert result.blockers


def test_strict_mode_includes_supporting_gate(config_file):
    relaxed = validate_checklist(config_file(BASE_CONFIG), strict=False)
    strict = validate_checklist(config_file(BASE_CONFIG), strict=True)

    assert relaxed.passed is True
    assert relaxed.total_gates == 1
    assert strict.passed is False
    assert strict.total_gates == 2
    assert strict.failed_count == 1


def test_domain_override_is_descriptive_and_injects_no_gates(config_file):
    path = config_file(BASE_CONFIG)
    normal = validate_checklist(path)
    overridden = validate_checklist(path, industry_override="healthcare")

    assert normal.domain_context == "library-operations"
    assert overridden.domain_context == "healthcare"
    assert [gate.gate for gate in normal.gates] == [gate.gate for gate in overridden.gates]


def test_high_risk_label_does_not_inject_generic_approval_gates(config_file):
    high = deepcopy(BASE_CONFIG)
    high["metadata"]["risk_classification"] = "high"

    result = validate_checklist(config_file(high))

    assert result.passed is True
    assert [gate.gate for gate in result.gates] == ["AUTH-001", "EVAL-001"]


def test_invalid_yaml_raises(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("{invalid: yaml: content: [}", encoding="utf-8")

    with pytest.raises(ChecklistValidationError, match="Invalid YAML"):
        validate_checklist(path)
