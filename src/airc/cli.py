"""Command-line interface for the airc release readiness checker."""
import sys
import click
from pathlib import Path
from airc.validator import validate_checklist, ChecklistValidationError
from airc.report import render_report


@click.group()
@click.version_option()
def main():
    """airc — AI Release Readiness Checker.

    Validate YAML-based release readiness configurations for AI/ML systems
    before deploying to regulated production environments.

    Aligned with NIST AI RMF (AI RMF 1.0) Measure function.

    \b
    Examples:
        airc validate release-checklist.yaml
        airc validate release-checklist.yaml --strict
        airc report release-checklist.yaml --format markdown
        airc init --industry healthcare
    """
    pass


@main.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Fail if any gates are not explicitly set to true (default: warn only).",
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
def validate(config_path: Path, strict: bool, output: str, industry: str):
    """Validate a release readiness configuration file.

    CONFIG_PATH: Path to a YAML release checklist configuration file.

    \b
    Returns exit code:
        0 — All required gates pass
        1 — Validation failed (missing required gates)
        2 — Configuration file is invalid YAML or missing required sections
    """
    try:
        result = validate_checklist(config_path, strict=strict, industry_override=industry)
        render_report(result, output_format=output)

        if result.passed:
            click.echo("\n✅ Release readiness check PASSED", err=True)
            sys.exit(0)
        else:
            click.echo(f"\n❌ Release readiness check FAILED — {result.failed_count} gate(s) not satisfied", err=True)
            sys.exit(1)

    except ChecklistValidationError as e:
        click.echo(f"\n❌ Configuration error: {e}", err=True)
        sys.exit(2)
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        sys.exit(2)


@main.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "markdown", "json"]),
    default="markdown",
    help="Report output format (default: markdown).",
)
def report(config_path: Path, fmt: str):
    """Generate a release readiness report from a configuration file.

    CONFIG_PATH: Path to a YAML release checklist configuration file.
    """
    try:
        result = validate_checklist(config_path)
        render_report(result, output_format=fmt, full_report=True)
    except ChecklistValidationError as e:
        click.echo(f"\n❌ Configuration error: {e}", err=True)
        sys.exit(2)


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
def init(industry: str, output: str):
    """Generate a new release checklist configuration template.

    Creates a YAML configuration file pre-configured for your target industry.
    """
    from airc.templates import get_template
    template = get_template(industry)
    output_path = Path(output)
    output_path.write_text(template)
    click.echo(f"\n✅ Created {output} for {industry} industry.")
    click.echo(f"   Edit the file and run: airc validate {output}")
