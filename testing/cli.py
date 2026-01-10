#!/usr/bin/env python3
"""
Skill Validation CLI

Usage:
    python -m testing.cli validate --skill langgraph
    python -m testing.cli validate --all
    python -m testing.cli check-imports --skill langgraph
"""

import sys
from pathlib import Path

try:
    import click
except ImportError:
    print("Please install click: pip install click")
    sys.exit(1)

from .validator import SkillValidator, format_result
from .imports import validate_imports, format_import_issues


# Find skills directory relative to this file
TESTING_DIR = Path(__file__).parent
ROOT_DIR = TESTING_DIR.parent
SKILLS_DIR = ROOT_DIR / "skills"


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Skill correctness validation CLI."""
    pass


@cli.command()
@click.option("--skill", help="Skill to validate (e.g., langgraph)")
@click.option("--all", "validate_all", is_flag=True, help="Validate all skills")
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
def validate(skill, validate_all, strict):
    """Validate skill content for correctness.

    Checks:
    - Python syntax in code blocks
    - Known anti-patterns (Pydantic for state, etc.)
    - Deprecated APIs
    - Missing critical sections
    """
    validator = SkillValidator()

    if validate_all:
        results = validator.validate_all_skills(SKILLS_DIR)
    elif skill:
        skill_path = SKILLS_DIR / skill / "SKILL.md"
        if not skill_path.exists():
            click.echo(f"Skill not found: {skill}", err=True)
            click.echo(f"Available skills: {', '.join(s.name for s in SKILLS_DIR.iterdir() if s.is_dir())}")
            sys.exit(1)
        results = [validator.validate_skill(skill_path)]
    else:
        click.echo("Specify --skill NAME or --all", err=True)
        sys.exit(1)

    # Print results
    total_errors = 0
    total_warnings = 0

    for result in results:
        click.echo(format_result(result))
        total_errors += result.error_count
        total_warnings += result.warning_count

    # Summary
    click.echo(f"\n{'='*60}")
    click.echo("SUMMARY")
    click.echo(f"{'='*60}")
    click.echo(f"Skills checked: {len(results)}")
    click.echo(f"Errors: {total_errors}")
    click.echo(f"Warnings: {total_warnings}")

    # Exit code
    if total_errors > 0:
        click.echo("\nFAILED - fix errors above")
        sys.exit(1)
    elif strict and total_warnings > 0:
        click.echo("\nFAILED (strict mode) - fix warnings above")
        sys.exit(1)
    else:
        click.echo("\nPASSED")


@cli.command("check-imports")
@click.option("--skill", required=True, help="Skill to check")
def check_imports(skill):
    """Check import statements in skill code blocks.

    Validates that imports reference current LangChain/LangGraph modules.
    """
    skill_path = SKILLS_DIR / skill / "SKILL.md"
    if not skill_path.exists():
        click.echo(f"Skill not found: {skill}", err=True)
        sys.exit(1)

    content = skill_path.read_text()

    # Extract code blocks
    import re
    code_blocks = re.findall(r"```(?:python|py)?\n(.*?)```", content, re.DOTALL)

    click.echo(f"Checking imports in {skill}...")
    click.echo(f"Found {len(code_blocks)} code blocks\n")

    all_issues = []
    for i, code in enumerate(code_blocks, 1):
        issues = validate_imports(code)
        if issues:
            click.echo(f"Block {i}:")
            click.echo(format_import_issues(issues))
            click.echo()
            all_issues.extend(issues)

    if not all_issues:
        click.echo("No import issues found!")
    else:
        click.echo(f"\nTotal: {len(all_issues)} import issues")


@cli.command("list-rules")
def list_rules():
    """List all validation rules."""
    validator = SkillValidator()

    click.echo("Validation Rules")
    click.echo("=" * 60)

    for rule in validator.rules:
        level = "ERROR" if rule["level"] == "error" else "WARN"
        click.echo(f"\n[{level}] {rule['id']}")
        click.echo(f"  {rule['message']}")
        if rule.get("suggestion"):
            click.echo(f"  Fix: {rule['suggestion']}")


@cli.command("quick")
def quick():
    """Quick validation of all skills - just show pass/fail."""
    validator = SkillValidator()
    results = validator.validate_all_skills(SKILLS_DIR)

    click.echo("Quick Validation")
    click.echo("=" * 40)

    all_passed = True
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        icon = "✓" if result.passed else "✗"
        details = ""
        if result.error_count:
            details = f" ({result.error_count} errors)"
        elif result.warning_count:
            details = f" ({result.warning_count} warnings)"

        click.echo(f"  {icon} {result.skill_name}: {status}{details}")

        if not result.passed:
            all_passed = False

    click.echo()
    if all_passed:
        click.echo("All skills passed!")
    else:
        click.echo("Some skills have errors. Run 'validate --all' for details.")
        sys.exit(1)


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
