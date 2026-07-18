from __future__ import annotations

from copy import deepcopy

import yaml

from airc.validator import validate_checklist


MINIMAL_CONFIG = {
    "metadata": {
        "project": "test-project",
        "version": "1.0.0",
        "environment": "staging",
        "domain_context": "general",
        "risk_classification": "low",
        "decision_scope": "Fictional internal read-only pilot",
        "decision_owner": "Fictional Sponsor",
        "evidence_cutoff": "2026-10-15",
    },
    "decision": {
        "outcome": "release_with_conditions",
        "rationale": "The fictional evidence supports only the bounded pilot.",
        "blockers": [],
        "required_actions": [],
        "conditions": ["Keep the pilot read-only."],
        "evidence_gaps": [],
        "residual_risks": [],
    },
    "gates": [
        {
            "id": "AUTH-001",
            "question": "Is write authority disabled?",
            "hard_gate": True,
            "status": "pass",
            "evidence": ["evidence/fictional-auth-test.json"],
            "owner": "Fictional Platform Owner",
            "limitation": "Pilot configuration only.",
        },
        {
            "id": "EVAL-001",
            "question": "Does supporting evaluation evidence cover the pilot?",
            "hard_gate": False,
            "status": "pass",
            "evidence": ["evidence/fictional-evaluation.md"],
            "owner": "Fictional Evaluation Owner",
            "limitation": "Pilot population only.",
        },
    ],
}


def write_config(tmp_path, config):
    path = tmp_path / "checklist.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path


def test_strict_mode_ignores_non_contract_free_form_metadata(tmp_path):
    config = deepcopy(MINIMAL_CONFIG)
    config["metadata"]["review_note"] = "Awaiting the next routine evidence refresh."

    result = validate_checklist(write_config(tmp_path, config), strict=True)

    assert result.passed
    assert {gate.gate for gate in result.gates} == {"AUTH-001", "EVAL-001"}


def test_explicit_pass_status_satisfies_declared_hard_gate(tmp_path):
    result = validate_checklist(write_config(tmp_path, deepcopy(MINIMAL_CONFIG)))

    assert result.passed
    assert result.unresolved_gates == []


def test_partial_status_never_satisfies_a_hard_gate(tmp_path):
    config = deepcopy(MINIMAL_CONFIG)
    config["gates"][0]["status"] = "partial"

    result = validate_checklist(write_config(tmp_path, config))

    assert not result.passed
    assert result.failed_count == 1
    assert [gate.gate for gate in result.unresolved_gates] == ["AUTH-001"]
