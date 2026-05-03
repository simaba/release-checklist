# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] — Foundation release

### Added

- Packaged `release-checklist` CLI for validating YAML-based AI release-readiness configurations.
- Risk-tiered gate requirements for low, medium, and high risk systems.
- Example configurations for medium-risk and high-risk releases.
- Template generation through `release-checklist init`.
- Text, JSON, and Markdown report rendering.
- CI workflow covering supported Python versions and packaged CLI behavior.
- Tests for validator behavior, required gates, metadata, strict mode, and invalid YAML.

### Improved

- Validator enforces required top-level sections and metadata fields.
- Validator enforces allow-listed environment, industry, and risk-tier values.
- Validator checks mapping/object shape for known structural sections.
- Validator enforces boolean types for known gates.
- Validator enforces bounded numeric values for known threshold fields.
- Metadata is excluded from gate accounting so strict mode focuses on actual release-readiness gates.

### Notes

This is a lightweight release-readiness validator, not a full policy engine. It is designed to provide repeatable local and CI-friendly checks that can support broader release governance workflows.
