# AI Release Readiness Checklist

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/simaba/ai-release-readiness-checklist)](https://github.com/simaba/ai-release-readiness-checklist/commits/main)

A practical, risk-tiered checklist framework for evaluating AI release readiness — with a lightweight CLI evaluation tool.

AI systems need release readiness checks that go beyond ordinary software quality gates: model behaviour, fallback paths, observability, and accountability all require explicit verification.

---

## How it works

Three risk tiers — choose based on safety impact, regulatory exposure, and reversibility:

| Tier | Use when |
|------|---------|
| **Low risk** | Internal tools, no safety impact, easily reversible |
| **Medium risk** | Customer-facing, some regulatory context, limited fallback |
| **High risk** | Safety-critical, regulated environment, hard to reverse |

Higher tiers include all requirements from lower tiers, plus additional items.

---

## Quick start

```bash
git clone https://github.com/simaba/ai-release-readiness-checklist.git
cd ai-release-readiness-checklist
pip install -r requirements.txt

# Evaluate against a medium-risk configuration
python src/check_release.py configs/medium-risk-example.yaml
```

**Example output:**
```
AI Release Readiness Evaluation
================================
Risk tier: medium  |  Checking 24 items...

  ✓ Model evaluation completed on held-out test set
  ✓ Baseline performance documented
  ✓ Fallback behaviour defined and tested
  ✗ Bias and fairness assessment not completed
  ...

Result: NOT READY — 3 items require attention
```

---

## Repository structure

```
checklists/
  low-risk.md               # Checklist for low-risk AI features
  medium-risk.md            # Checklist for medium-risk AI features
  high-risk.md              # Checklist for high-risk AI features
configs/
  medium-risk-example.yaml  # Example YAML configuration
  high-risk-example.yaml    # Example YAML configuration
src/
  check_release.py          # CLI evaluation tool
requirements.txt
```

---

## Customising for your team

1. Fork the repository
2. Edit the checklist `.md` files to match your organisation's requirements
3. Update the YAML configs to reflect your feature's risk profile
4. Run `check_release.py` as part of your release pipeline

---

## Companion repositories

- **[AI Release Governance Framework](https://github.com/simaba/ai-release-governance-framework)** — the broader framework this checklist operationalises
- **[Enterprise AI Governance Playbook](https://github.com/simaba/enterprise-ai-governance-playbook)** — where this checklist fits in the full operating lifecycle

---

## Related repositories

This repository is part of a connected toolkit for responsible AI operations:

| Repository | Purpose |
|-----------|---------|
| [Enterprise AI Governance Playbook](https://github.com/simaba/enterprise-ai-governance-playbook) | End-to-end AI operating model from intake to improvement |
| [AI Release Governance Framework](https://github.com/simaba/ai-release-governance-framework) | Risk-based release gates for AI systems |
| [AI Release Readiness Checklist](https://github.com/simaba/ai-release-readiness-checklist) | Risk-tiered pre-release checklists with CLI tool |
| [AI Accountability Design Patterns](https://github.com/simaba/ai-accountability-design-patterns) | Patterns for human oversight and escalation |
| [Multi-Agent Governance Framework](https://github.com/simaba/multi-agent-governance-framework) | Roles, authority, and escalation for agent systems |
| [Multi-Agent Orchestration Patterns](https://github.com/simaba/multi-agent-orchestration-patterns) | Sequential, parallel, and feedback-loop patterns |
| [AI Agent Evaluation Framework](https://github.com/simaba/ai-agent-evaluation-framework) | System-level evaluation across 5 dimensions |
| [Agent System Simulator](https://github.com/simaba/agent-system-simulator) | Runnable multi-agent simulator with governance controls |
| [LLM-powered Lean Six Sigma](https://github.com/simaba/LLM-powered-Lean-Six-Sigma) | AI copilot for structured process improvement |

---

*Shared in a personal capacity. Open to collaborations and feedback — connect on [LinkedIn](https://linkedin.com/in/simaba) or [Medium](https://medium.com/@bagheri.sima).*
