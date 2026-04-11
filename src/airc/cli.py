"""Command-line interface for the release-checklist validator."""

from __future__ import annotations

from pathlib import Path

import click

from airc.report import render_report
from airc.validator import ChecklistValidationError, validate_checklist


@click.group()
@click.version_option()
def main() -> None:
    """release-checklist, a validator for AI release readiness.

    Validate YAML-based release readiness configurations for AI/ML systems
    before deploying to regulated production environments.

    Aligned with NIST AI RMF (AI RMF 1.0) Measure function.

    Examples:
        release-checklist validate release-checklist.yaml
        release-checklist validate release-checklist.yaml --strict
        release-checklist report release-checklist.yaml --format markdown
        release-checklist init --industry healthcare
    """


@main.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Fail if optional boolean gates are not explicitly set to true.",
)
@click.option(
    "--output",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format (default: text).",
)
@click.option(
    "--industry",
    type=click.Choice(["healthcare", "finance", "insurance", "government", "general"]),
    default=None,
    help="Override industry-specific gate requirements.",
)
def validate(config_path: Path, strict: bool, output: str, industry: str | None) -> None:
    """Validate a release readiness configuration file."""
    try:
        result = validate_checklist(config_path, strict=strict, industry_override=industry)
        render_report(result, output_format=output)

        if result.passed:
            click.echo("\n✅ Release readiness check PASSED", err=True)
            raise SystemExit(0)

        click.echo(
            f"\n❌ Release readiness check FAILED, {result.failed_count} gate(s) not satisfied",
            err=True,
        )
        raise SystemExit(1)

    except ChecklistValidationError as exc:
        click.echo(f"\n❌ Configuration error: {exc}", err=True)
        raise SystemExit(2) from exc
    except Exception as exc:  # pragma: no cover - defensive CLI fallback
        click.echo(f"\n❌ Unexpected error: {exc}", err=True)
        raise SystemExit(2) from exc


@main.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "markdown", "json"]),
    default="markdown",
    help="Report output format (default: markdown).",
)
def report(config_path: Path, fmt: str) -> None:
    """Generate a release readiness report from a configuration file."""
    try:
        result = validate_checklist(config_path)
        render_report(result, output_format=fmt, full_report=True)
    except ChecklistValidationError as exc:
        click.echo(f"\n❌ Configuration error: {exc}", err=True)
        raise SystemExit(2) from exc


@main.command()
@click.option(
    "--industry",
    type=click.Choice(["healthcare", "finance", "insurance", "government", "general"]),
    default="general",
    prompt="Target industry",
    help="Industry to optimize the template for.",
)
@click.option(
    "--output",
    "-o",
    default="release-checklist.yaml",
    help="Output filename (default: release-checklist.yaml).",
)
def init(industry: str, output: str) -> None:
    """Generate a new release checklist configuration template."""
    from airc.templates import get_template

    template = get_template(industry)
    output_path = Path(output)
    output_path.write_text(template, encoding="utf-8")
    click.echo(f"\n✅ Created {output} for {industry} industry.")
    click.echo(f"   Edit the file and run: release-checklist validate {output}")


if __name__ == "__main__":
    main()
