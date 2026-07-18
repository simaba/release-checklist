# AI Release Decision Validator

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/simaba/release-checklist)](https://github.com/simaba/release-checklist/commits/main)

A packaged CLI for validating the **structure and internal coherence of a bounded AI release-decision record**.

The tool does not decide which controls a healthcare, financial, automotive, public-sector, or other system requires. It requires the team to declare its own decision-relevant propositions, mark non-compensable hard gates, cite evidence, disclose limitations, and record the resulting outcome.

## Why this model

A generic checklist can create false assurance:

- “bias evaluation complete” does not identify the population, metric, method, or result;
- “legal approved” does not explain the decision scope or applicable question;
- one universal accuracy threshold is not meaningful across tasks;
- an industry label cannot safely inject the right obligations;
- a weighted score should not override a failed authorization or safety boundary.

This validator therefore checks a narrower contract: **is the supplied release record identifiable, evidence-bearing, and logically consistent with its stated outcome?**

## What the CLI validates

- required metadata, including decision scope, owner, version, and evidence cutoff;
- semantic-version and ISO-date formatting;
- recursive placeholder removal;
- unique gate identifiers and valid gate statuses;
- evidence references for `pass` and `not_applicable` gates;
- scoped rationale for `not_applicable`;
- separation of hard gates from supporting gates;
- decision semantics for `release`, `release_with_conditions`, `hold`, `do_not_release`, and `defer`;
- blockers, conditions, required actions, evidence gaps, and residual risks;
- text, Markdown, and JSON reporting.

It does **not** authenticate evidence, determine legal applicability, decide whether a gate is appropriate, accept residual risk, or certify safety/compliance.

## Quick start

```bash
git clone https://github.com/simaba/release-checklist.git
cd release-checklist
python -m pip install -e .

release-checklist validate configs/medium-risk-example.yaml
release-checklist report configs/medium-risk-example.yaml --format markdown
```

The medium example is a fictional conditional pilot that returns exit code `0`. The high-risk example is a fictional coherent `hold` decision and therefore returns exit code `1` from `validate`, while `report` still renders the full record.

```bash
release-checklist report configs/high-risk-example.yaml --format markdown
```

## Configuration contract

```yaml
metadata:
  project: "Fictional Assistant"
  version: "1.0.0-pilot"
  environment: "staging"
  risk_classification: "medium"
  domain_context: "library-operations"
  decision_scope: "20 trained staff; public records; read and draft tools only"
  decision_owner: "Fictional Sponsor"
  evidence_cutoff: "2026-10-15"

decision:
  outcome: "release_with_conditions"
  rationale: "The evidence supports only the bounded pilot."
  blockers: []
  required_actions:
    - "Complete a larger rare-record sample before expansion."
  conditions:
    - "Keep all tools read-only."
  evidence_gaps:
    - "Rare-record coverage remains limited."
  residual_risks:
    - "Users may over-trust fluent drafts."

gates:
  - id: "AUTH-001"
    question: "Is write authority disabled for the reviewed scope?"
    hard_gate: true
    status: "pass"
    evidence:
      - "evidence/fictional-authority-test.json"
    owner: "Fictional Platform Owner"
    limitation: "Pilot configuration only."
```

Gate status values:

- `pass`
- `fail`
- `partial`
- `not_tested`
- `not_applicable`

A hard gate is non-compensable for the declared scope. `pass` and `not_applicable` must cite evidence; `not_applicable` also needs a scoped rationale.

## Decision outcomes

| Outcome | Validator interpretation |
|---|---|
| `release` | No declared blockers, no unresolved hard gates, and no accepted conditions or required actions |
| `release_with_conditions` | No declared blockers or unresolved hard gates; at least one condition or required action |
| `hold` | Valid record, but the current state does not authorize release |
| `do_not_release` | Requires a declared blocker or unresolved hard gate |
| `defer` | Requires at least one evidence gap explaining why a decision cannot yet be made |

The `validate` command returns exit code `0` only for supported `release` or `release_with_conditions` outcomes. It returns `1` for coherent hold/defer/do-not-release records and for release outcomes blocked by hard gates. Invalid configuration returns `2`.

## Strict mode

By default, only hard gates determine whether a release outcome is supported. Supporting gates remain visible in reports but may be `partial` without blocking the bounded decision.

```bash
release-checklist validate configs/medium-risk-example.yaml --strict
```

Strict mode requires every declared supporting gate to be `pass` or `not_applicable`. It is a review convenience, not a universal policy recommendation.

## Template generation

```bash
release-checklist init --domain healthcare -o release-decision.yaml
```

`--industry` remains as a backward-compatible alias:

```bash
release-checklist init --industry healthcare
```

The label is descriptive context only. It does **not** inject HIPAA, SR 11-7, legal-review, fairness, security, or other gates. Derive propositions from the actual system, authority, harm model, policy, and qualified review.

## Python API compatibility

The internal package namespace remains `airc`. Existing callers can continue using:

```python
from airc.validator import validate_checklist

result = validate_checklist(path, industry_override="healthcare")
```

`industry_override` now changes only the reported domain context. The compatibility field `result.regulated_industry` remains available; `result.domain_context` is the preferred name.

## Repository structure

```text
configs/                 fictional decision examples
src/airc/validator.py    structure and decision semantics
src/airc/report.py       text, Markdown, and JSON rendering
src/airc/templates.py    domain-neutral starter template
src/airc/cli.py          packaged command-line interface
tests/                   decision-contract tests
.github/workflows/ci.yml Python matrix, CLI smoke tests, package build
```

## Scope

This is an alpha governance utility. Schema and decision coherence are useful controls, but they do not establish that:

- evidence is authentic, current, representative, or sufficient;
- a gate is legally or technically appropriate;
- a condition is enforceable;
- the named owner has valid authority;
- a release is safe, compliant, production-ready, or valuable.

Use qualified engineering, safety, security, privacy, legal, compliance, operations, accessibility, and domain review where the real system requires it.

## Related repositories

- [`release-governance`](https://github.com/simaba/release-governance) — release lifecycle and decision-record methodology.
- [`governance-playbook`](https://github.com/simaba/governance-playbook) — wider organizational decision and evidence service.
- [`regulated-ai`](https://github.com/simaba/regulated-ai) — starter repository with a compatible evidence-based decision example.

---

*Maintained by [Sima Bagheri](https://github.com/simaba).*
