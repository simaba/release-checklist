# AI Release Readiness Checklist

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/simaba/release-checklist)](https://github.com/simaba/release-checklist/commits/main)

A practical, risk-tiered checklist framework for evaluating AI release readiness, with a packaged CLI validator for local use and CI pipelines.

AI systems need release readiness checks that go beyond ordinary software quality gates. Model behaviour, fallback paths, observability, and accountability all require explicit verification.

---

## What this repository provides

- A packaged `release-checklist` CLI for validating YAML-based release gate configurations
- Starter templates generated with `release-checklist init`
- Example configurations for medium-risk and high-risk AI systems
- A validation model aligned to technical, governance, infrastructure, and incident-readiness checks

---

## How it works

Three risk tiers are supported, chosen based on safety impact, regulatory exposure, and reversibility:

| Tier | Use when |
|------|---------|
| **Low risk** | Internal tools, no safety impact, easily reversible |
| **Medium risk** | Customer-facing, some regulatory context, limited fallback |
| **High risk** | Safety-critical, regulated environment, hard to reverse |

Higher tiers inherit the required gates from lower tiers and add stricter requirements.

The validator expects a nested YAML structure with these top-level sections:

- `metadata`
- `model_validation`
- `governance`
- `infrastructure`
- optional but supported: `incident_readiness`

---

## Quick start

```bash
git clone https://github.com/simaba/release-checklist.git
cd release-checklist
python -m pip install -e .
```

Validate a working example configuration:

```bash
release-checklist validate configs/medium-risk-example.yaml
```

Generate a report:

```bash
release-checklist report configs/medium-risk-example.yaml --format markdown
```

Create a starter template:

```bash
release-checklist init --industry healthcare
```

Legacy direct execution is still supported for local source checkouts:

```bash
python src/check_release.py validate configs/medium-risk-example.yaml
```

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

**Example output:**
```text
✅ Release readiness check PASSED
```

---

## Example configuration shape

```yaml
metadata:
  project: "IVI assistant"
  version: "1.0.0"
  environment: "staging"
  regulated_industry: "general"
  risk_classification: "medium"

model_validation:
  performance:
    accuracy_threshold: 0.90
    bias_evaluation_complete: true

governance:
  documentation:
    risk_assessment_complete: true
  approvals:
    technical_review: true

infrastructure:
  testing:
    unit_tests_passing: true
  rollback:
    rollback_plan_documented: true
```

Use `release-checklist init` when starting from scratch so your file structure stays aligned to the validator.

---

## Repository structure

```text
configs/
  medium-risk-example.yaml  # Example YAML configuration
  high-risk-example.yaml    # Example YAML configuration
src/
  airc/
    cli.py                  # Packaged CLI entry point
    validator.py            # Core validation logic
    report.py               # Text / JSON / Markdown reporting
    templates.py            # Template generation for `release-checklist init`
  check_release.py          # Legacy compatibility wrapper
tests/
  test_validator.py
requirements.txt
pyproject.toml
```

---

## Customising for your team

1. Fork the repository.
2. Generate a baseline file with `release-checklist init`.
3. Adjust the YAML values to match your industry, system risk, and internal approval model.
4. Run `release-checklist validate` in CI before deployment.

---

## Companion repositories

- **[AI Release Governance Framework](https://github.com/simaba/release-governance)** for the broader framework this checklist operationalises.
- **[Enterprise AI Governance Playbook](https://github.com/simaba/governance-playbook)** for where this checklist fits in the full operating lifecycle.

---

## Related repositories

This repository is part of a connected toolkit for responsible AI operations:

| Repository | Purpose |
|-----------|---------|
| [Enterprise AI Governance Playbook](https://github.com/simaba/governance-playbook) | End-to-end AI operating model from intake to improvement |
| [AI Release Governance Framework](https://github.com/simaba/release-governance) | Risk-based release gates for AI systems |
| [AI Release Readiness Checklist](https://github.com/simaba/release-checklist) | Risk-tiered pre-release checklists with CLI tool |
| [AI Accountability Design Patterns](https://github.com/simaba/accountability-patterns) | Patterns for human oversight and escalation |
| [Multi-Agent Governance Framework](https://github.com/simaba/multi-agent-governance) | Roles, authority, and escalation for agent systems |
| [Multi-Agent Orchestration Patterns](https://github.com/simaba/agent-orchestration) | Sequential, parallel, and feedback-loop patterns |
| [AI Agent Evaluation Framework](https://github.com/simaba/agent-eval) | System-level evaluation across 5 dimensions |
| [Agent System Simulator](https://github.com/simaba/agent-simulator) | Runnable multi-agent simulator with governance controls |
| [LLM-powered Lean Six Sigma](https://github.com/simaba/lean-ai-ops) | AI copilot for structured process improvement |

---

*Shared in a personal capacity. Open to collaborations and feedback. Connect on [LinkedIn](https://linkedin.com/in/simaba) or [Medium](https://medium.com/@bagheri.sima).*