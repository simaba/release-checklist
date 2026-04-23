# AI Release Readiness Checklist

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/simaba/release-checklist)](https://github.com/simaba/release-checklist/commits/main)

A practical, risk-tiered checklist framework for evaluating AI release readiness, with a packaged CLI validator for local use and CI pipelines.

## Choose this repo when

Use this repository when you need a **working validator** for YAML-based release-readiness configurations.

This repo is intentionally narrower than:

- [`release-governance`](https://github.com/simaba/release-governance), which explains the broader release lifecycle and gate model
- [`governance-playbook`](https://github.com/simaba/governance-playbook), which covers the wider AI operating model
- [`regulated-ai`](https://github.com/simaba/regulated-ai), which is a starter template repo

## What this repository provides

- a packaged `release-checklist` CLI for validating YAML-based release gate configurations
- starter templates generated with `release-checklist init`
- example configurations for medium-risk and high-risk AI systems
- typed validation for known metadata fields, boolean gates, bounded numeric values, and expected mapping shapes
- text, JSON, and Markdown reporting for local use and CI pipelines
- GitHub Actions CI covering supported Python versions and packaged CLI behavior

## How it works

Three risk tiers are supported, chosen based on safety impact, regulatory exposure, and reversibility:

| Tier | Use when |
|---|---|
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

Known nested sections such as `model_validation.performance`, `governance.approvals`, and `infrastructure.testing` are expected to be mappings rather than free-form lists or strings.

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

## Validation behavior

The validator currently enforces:

- required top-level sections
- required metadata fields
- allow-listed values for environment, industry, and risk tier
- semver-like version formatting such as `1.0.0`
- mapping/object shape checks for known structural sections
- boolean typing for known gates
- bounded numeric validation for known fields such as `accuracy_threshold`
- positive numeric validation for known monitoring fields such as `latency_ms`

This repository is meant to be useful in real workflows, but it is still a lightweight validator rather than a full policy engine.

## Repository structure

```text
configs/
  medium-risk-example.yaml
  high-risk-example.yaml
src/
  airc/
    cli.py
    validator.py
    report.py
    templates.py
  check_release.py
tests/
  test_validator.py
requirements.txt
pyproject.toml
.github/workflows/ci.yml
```

## Related repositories

| Repository | What it adds |
|---|---|
| [release-governance](https://github.com/simaba/release-governance) | Broader framework this checklist operationalizes |
| [governance-playbook](https://github.com/simaba/governance-playbook) | End-to-end operating model |
| [regulated-ai](https://github.com/simaba/regulated-ai) | Starter template repo with governance artifacts |

---

*Shared in a personal capacity. Open to collaborations and feedback via [LinkedIn](https://linkedin.com/in/simaba) or [Medium](https://medium.com/@bagheri.sima).*
