"""Command-line interface for the release-checklist validator."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from airc.report import render_report
from airc.validator import ChecklistValidationError, validate_checklist


@click.group()
@click.version_option()
def main() -> None:
    """Validate scoped AI release-decision records.

    The CLI checks YAML structure, evidence references, hard-gate state, and
    selected decision coherence. It does not certify safety, compliance, or
    production readiness.
    """


@main.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Require every declared supporting gate, not only hard gates, to pass.",
)
@click.option(
    "--output",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format (default: text).",
)
@click.option(
    "--domain",
    "--industry",
    "domain_context",
    default=None,
    help=(
        "Override descriptive domain context. The legacy --industry alias is "
        "retained, but no domain-specific gates are injected."
    ),
)
def validate(
    config_path: Path,
    strict: bool,
    output: str,
    domain_context: Optional[str],
) -> None:
    """Validate a release-decision configuration file."""
    try:
        result = validate_checklist(
            config_path,
            strict=strict,
            industry_override=domain_context,
        )
        render_report(result, output_format=output)

        if result.passed:
            click.echo(
                f"\n✅ Decision record supports outcome: {result.outcome}",
                err=True,
            )
            raise SystemExit(0)

        click.echo(
            f"\n❌ Decision record does not support release; outcome={result.outcome}, "
            f"unresolved={result.failed_count}",
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
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Include every supporting gate in the decision status.",
)
def report(config_path: Path, fmt: str, strict: bool) -> None:
    """Generate a detailed report from a release-decision record."""
    try:
        result = validate_checklist(config_path, strict=strict)
        render_report(result, output_format=fmt, full_report=True)
    except ChecklistValidationError as exc:
        click.echo(f"\n❌ Configuration error: {exc}", err=True)
        raise SystemExit(2) from exc


@main.command()
@click.option(
    "--domain",
    "--industry",
    "domain_context",
    default="general",
    prompt="Domain context",
    help=(
        "Descriptive domain label for the generated template. The legacy "
        "--industry alias remains supported."
    ),
)
@click.option(
    "--output",
    "-o",
    default="release-checklist.yaml",
    help="Output filename (default: release-checklist.yaml).",
)
def init(domain_context: str, output: str) -> None:
    """Generate a domain-labelled, evidence-based decision template."""
    from airc.templates import get_template

    template = get_template(domain_context)
    output_path = Path(output)
    output_path.write_text(template, encoding="utf-8")
    click.echo(f"\n✅ Created {output} with domain context '{domain_context}'.")
    click.echo(f"   Replace placeholders, then run: release-checklist validate {output}")


if __name__ == "__main__":
    main()
