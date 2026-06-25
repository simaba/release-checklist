"""Report rendering for release-checklist validation results."""

from __future__ import annotations

import json
from typing import List

from airc.validator import GateResult, ValidationResult


def _report_scope(result: ValidationResult) -> List[GateResult]:
    """Return the gates that determine the displayed release decision."""
    if result.strict:
        return result.gates
    return [gate for gate in result.gates if gate.required]


def render_report(
    result: ValidationResult,
    output_format: str = "text",
    full_report: bool = False,
) -> None:
    """Render a validation result to stdout."""
    if output_format == "json":
        _render_json(result)
    elif output_format == "markdown":
        _render_markdown(result, full_report)
    else:
        _render_text(result, full_report)


def _render_text(result: ValidationResult, full_report: bool) -> None:
    scope = _report_scope(result)
    scope_label = "Declared Gates" if result.strict else "Required Gates"
    divider = "=" * 60

    print("\n{}".format(divider))
    print("  AI Release Readiness Report")
    print("  Project: {} v{}".format(result.project, result.version))
    print("  Environment: {}".format(result.environment))
    print(
        "  Industry: {} | Risk: {}".format(
            result.regulated_industry,
            result.risk_classification,
        )
    )
    print("  Mode: {}".format("strict" if result.strict else "required gates"))
    print(divider)

    print(
        "\n{}: {}/{} satisfied".format(
            scope_label,
            result.passed_count,
            result.total_gates,
        )
    )

    failed = [gate for gate in scope if not gate.passed]
    if failed:
        print("\n❌ Failed {}:".format(scope_label))
        for gate in failed:
            print("   • {} (current: {})".format(gate.gate, gate.value))

    if full_report:
        print("\n✅ Passing Gates:")
        for gate in result.gates:
            if gate.passed:
                status = "REQUIRED" if gate.required else "optional"
                print("   ✓ {} [{}]".format(gate.gate, status))


def _render_markdown(result: ValidationResult, full_report: bool) -> None:
    scope = _report_scope(result)
    scope_label = "Declared gates" if result.strict else "Required gates"
    failed = [gate for gate in scope if not gate.passed]
    lines = [
        "# Release Readiness Report",
        "",
        "| Field | Value |",
        "|---|---|",
        "| Project | {} v{} |".format(result.project, result.version),
        "| Environment | {} |".format(result.environment),
        "| Industry | {} |".format(result.regulated_industry),
        "| Risk Classification | {} |".format(result.risk_classification),
        "| Validation mode | {} |".format(
            "strict" if result.strict else "required gates"
        ),
        "| Status | {} |".format("✅ PASSED" if result.passed else "❌ FAILED"),
        "",
        "## Gate Summary",
        "",
        "- **Scope:** {}".format(scope_label),
        "- **Total gates:** {}".format(result.total_gates),
        "- **Passing:** {}".format(result.passed_count),
        "- **Failed:** {}".format(result.failed_count),
        "",
    ]

    if failed:
        lines += ["## ❌ Failed Gates", ""]
        for gate in failed:
            lines.append("- `{}` — current value: `{}`".format(gate.gate, gate.value))
        lines.append("")

    if full_report:
        lines += [
            "## All Gates",
            "",
            "| Gate | Value | Required | Status |",
            "|---|---|---|---|",
        ]
        for gate in result.gates:
            status = "✅" if gate.passed else "❌"
            required = "Required" if gate.required else "Optional"
            lines.append(
                "| `{}` | `{}` | {} | {} |".format(
                    gate.gate,
                    gate.value,
                    required,
                    status,
                )
            )

    print("\n".join(lines))


def _render_json(result: ValidationResult) -> None:
    scope = _report_scope(result)
    out = {
        "project": result.project,
        "version": result.version,
        "environment": result.environment,
        "regulated_industry": result.regulated_industry,
        "risk_classification": result.risk_classification,
        "strict": result.strict,
        "decision_scope": "declared_gates" if result.strict else "required_gates",
        "passed": result.passed,
        "passed_count": result.passed_count,
        "failed_count": result.failed_count,
        "total_gates": result.total_gates,
        "failed_gates": [gate.gate for gate in scope if not gate.passed],
        "gates": [
            {
                "gate": gate.gate,
                "value": gate.value,
                "passed": gate.passed,
                "required": gate.required,
            }
            for gate in result.gates
        ],
    }
    print(json.dumps(out, indent=2))
