# AI Release Readiness Checklist

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/simaba/release-checklist)](https://github.com/simaba/release-checklist/commits/main)

A practical, risk-tiered checklist framework for evaluating AI release readiness, with a packaged CLI validator for local use and CI pipelines.

AI systems need release readiness checks that go beyond ordinary software quality gates. Model behaviour, fallback paths, observability, and accountability all require explicit verification.

---

## How it works

Three risk tiers, chosen based on safety impact, regulatory exposure, and reversibility:

| Tier | Use when |
|------|---------|
| **Low risk** | Internal tools, no safety impact, easily reversible |
| **Medium risk** | Customer-facing, some regulatory context, limited fallback |
| **High risk** | Safety-critical, regulated environment, hard to reverse |

Higher tiers include all requirements from lower tiers, plus additional items.

---

## Quick start

```bash
git clone https://github.com/simaba/release-checklist.git
cd release-checklist
python -m pip install -e .
```

Validate an example configuration:

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

## Repository structure

```text
checklists/
  low-risk.md               # Checklist for low-risk AI features
  medium-risk.md            # Checklist for medium-risk AI features
  high-risk.md              # Checklist for high-risk AI features
configs/
  medium-risk-example.yaml  # Example YAML configuration
  high-risk-example.yaml    # Example YAML configuration
src/
  airc/
    cli.py                  # Packaged CLI entry point
    validator.py            # Core validation logic
    report.py               # Text / JSON / Markdown reporting
  check_release.py          # Legacy compatibility wrapper
tests/
  test_validator.py
requirements.txt
pyproject.toml
```

---

## Customising for your team

1. Fork the repository.
2. Edit the checklist `.md` files to match your organisation's requirements.
3. Update the YAML configs to reflect your feature's risk profile.
4. Run `release-checklist validate` as part of your release pipeline.

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