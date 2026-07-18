"""Report rendering for release-decision validation results."""

from __future__ import annotations

import json
from typing import List

from airc.validator import GateResult, ValidationResult


def _report_scope(result: ValidationResult) -> List[GateResult]:
    if result.strict:
        return result.gates
    return [gate for gate in result.gates if gate.required]


def render_report(
    result: ValidationResult,
    output_format: str = "text",
    full_report: bool = False,
) -> None:
    """Render a validated release-decision record to stdout."""
    if output_format == "json":
        _render_json(result)
    elif output_format == "markdown":
        _render_markdown(result, full_report)
    else:
        _render_text(result, full_report)


def _append_text_section(lines: List[str], title: str, values: List[str]) -> None:
    if values:
        lines.extend(["", f"{title}:"])
        lines.extend(f"  - {item}" for item in values)


def _render_text(result: ValidationResult, full_report: bool) -> None:
    scope = _report_scope(result)
    divider = "=" * 64
    lines = [
        "",
        divider,
        "  AI Release Decision Report",
        f"  Project: {result.project} v{result.version}",
        f"  Environment: {result.environment}",
        f"  Domain context: {result.domain_context}",
        f"  Risk classification: {result.risk_classification}",
        f"  Decision owner: {result.decision_owner}",
        f"  Evidence cutoff: {result.evidence_cutoff}",
        f"  Outcome: {result.outcome}",
        f"  Decision supported: {'YES' if result.passed else 'NO'}",
        divider,
        "",
        f"Scope: {result.decision_scope}",
        f"Rationale: {result.rationale}",
        "",
        f"Gate scope: {'all declared gates' if result.strict else 'hard gates only'}",
        f"Satisfied: {result.passed_count}/{result.total_gates}",
    ]

    failed = [gate for gate in scope if not gate.passed]
    if failed:
        lines.extend(["", "Unresolved gates:"])
        lines.extend(
            f"  - {gate.gate}: {gate.value} — {gate.question}"
            for gate in failed
        )

    _append_text_section(lines, "Blockers", result.blockers)
    _append_text_section(lines, "Conditions", result.conditions)
    _append_text_section(lines, "Required actions", result.required_actions)
    _append_text_section(lines, "Evidence gaps", result.evidence_gaps)
    _append_text_section(lines, "Residual risks", result.residual_risks)

    if full_report:
        lines.extend(["", "All declared gates:"])
        for gate in result.gates:
            label = "hard" if gate.required else "supporting"
            lines.append(
                f"  - {gate.gate}: {gate.value} [{label}] "
                f"evidence={len(gate.evidence)} owner={gate.owner}"
            )
    print("\n".join(lines))


def _append_markdown_list(lines: List[str], title: str, values: List[str]) -> None:
    if values:
        lines.extend([f"## {title}", ""])
        lines.extend(f"- {item}" for item in values)
        lines.append("")


def _render_markdown(result: ValidationResult, full_report: bool) -> None:
    scope = _report_scope(result)
    failed = [gate for gate in scope if not gate.passed]
    lines = [
        "# Release Decision Report",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Project | {result.project} v{result.version} |",
        f"| Environment | {result.environment} |",
        f"| Domain context | {result.domain_context} |",
        f"| Risk classification | {result.risk_classification} |",
        f"| Decision owner | {result.decision_owner} |",
        f"| Evidence cutoff | {result.evidence_cutoff} |",
        f"| Outcome | `{result.outcome}` |",
        f"| Decision supported | {'✅ YES' if result.passed else '❌ NO'} |",
        "",
        "## Decision scope",
        "",
        result.decision_scope,
        "",
        "## Rationale",
        "",
        result.rationale,
        "",
        "## Gate summary",
        "",
        f"- **Scope:** {'all declared gates' if result.strict else 'hard gates only'}",
        f"- **Total:** {result.total_gates}",
        f"- **Satisfied:** {result.passed_count}",
        f"- **Unresolved:** {sum(1 for gate in scope if not gate.passed)}",
        "",
    ]

    if failed:
        lines.extend(["## Unresolved gates", ""])
        for gate in failed:
            lines.append(
                f"- `{gate.gate}` — `{gate.value}` — {gate.question}"
            )
        lines.append("")

    _append_markdown_list(lines, "Blockers", result.blockers)
    _append_markdown_list(lines, "Conditions", result.conditions)
    _append_markdown_list(lines, "Required actions", result.required_actions)
    _append_markdown_list(lines, "Evidence gaps", result.evidence_gaps)
    _append_markdown_list(lines, "Residual risks", result.residual_risks)

    if full_report:
        lines.extend(
            [
                "## All declared gates",
                "",
                "| Gate | Status | Type | Evidence | Owner | Limitation |",
                "|---|---|---|---:|---|---|",
            ]
        )
        for gate in result.gates:
            lines.append(
                "| `{}` | `{}` | {} | {} | {} | {} |".format(
                    gate.gate,
                    gate.value,
                    "Hard" if gate.required else "Supporting",
                    len(gate.evidence),
                    gate.owner,
                    gate.limitation or "—",
                )
            )
    print("\n".join(lines))


def _render_json(result: ValidationResult) -> None:
    scope = _report_scope(result)
    out = {
        "project": result.project,
        "version": result.version,
        "environment": result.environment,
        "domain_context": result.domain_context,
        # Compatibility key retained for existing consumers.
        "regulated_industry": result.regulated_industry,
        "risk_classification": result.risk_classification,
        "decision_scope": result.decision_scope,
        "decision_owner": result.decision_owner,
        "evidence_cutoff": result.evidence_cutoff,
        "outcome": result.outcome,
        "rationale": result.rationale,
        "strict": result.strict,
        "gate_scope": "all_declared_gates" if result.strict else "hard_gates",
        "configuration_valid": result.configuration_valid,
        "passed": result.passed,
        "passed_count": result.passed_count,
        "failed_count": result.failed_count,
        "total_gates": result.total_gates,
        "failed_gates": [gate.gate for gate in scope if not gate.passed],
        "blockers": result.blockers,
        "conditions": result.conditions,
        "required_actions": result.required_actions,
        "evidence_gaps": result.evidence_gaps,
        "residual_risks": result.residual_risks,
        "gates": [
            {
                "id": gate.gate,
                "question": gate.question,
                "status": gate.value,
                "passed": gate.passed,
                "hard_gate": gate.required,
                "evidence": gate.evidence,
                "owner": gate.owner,
                "limitation": gate.limitation,
            }
            for gate in result.gates
        ],
    }
    print(json.dumps(out, indent=2))
