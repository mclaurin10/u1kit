"""CLI entry point for u1kit."""

from __future__ import annotations

import sys
from importlib.resources import as_file, files
from typing import Any

import click
import yaml

from u1kit.archive import read_3mf, write_3mf
from u1kit.config import emit_config, parse_config
from u1kit.fixers import get_fixer_map
from u1kit.fixers.base import FixMode, Pipeline
from u1kit.report import format_human, format_json
from u1kit.rules import RULES, get_rule
from u1kit.rules.base import Context, Result, Severity


def _load_preset(name: str) -> dict[str, Any]:
    """Load a preset YAML file by name."""
    # Try underscore form first (bambu_to_u1.yaml), then hyphenated
    for filename in (f"{name.replace('-', '_')}.yaml", f"{name}.yaml"):
        ref = files("u1kit.presets").joinpath(filename)
        try:
            with as_file(ref) as path:
                text = path.read_text(encoding="utf-8")
                result: Any = yaml.safe_load(text)
                return result  # type: ignore[no-any-return]
        except (FileNotFoundError, TypeError):
            continue

    click.echo(f"Error: preset {name!r} not found.", err=True)
    sys.exit(1)


def _list_presets() -> list[dict[str, str]]:
    """List available presets."""
    presets_pkg = files("u1kit.presets")
    result: list[dict[str, str]] = []

    for item in presets_pkg.iterdir():
        item_name = item.name
        if not item_name.endswith(".yaml"):
            continue
        try:
            text = item.read_text(encoding="utf-8")
        except (TypeError, AttributeError):
            continue
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            result.append({
                "name": data.get("name", item_name[:-5]),
                "description": data.get("description", ""),
            })
    return result


def _get_rules_for_preset(preset: dict[str, Any]) -> list[type[Any]]:
    """Get rule classes for a preset, always including A1."""
    from u1kit.rules.a1_source_slicer import A1SourceSlicer

    rule_ids = preset.get("rules", [])
    rules: list[type[Any]] = [A1SourceSlicer]

    for rule_id in rule_ids:
        try:
            rule_cls = get_rule(rule_id)
            if rule_cls not in rules:
                rules.append(rule_cls)
        except KeyError:
            click.echo(
                f"Warning: unknown rule {rule_id!r} in preset, skipping.",
                err=True,
            )

    return rules


@click.group()
def main() -> None:
    """u1kit — convert Bambu/Makerworld .3mf files for the Snapmaker U1."""


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "use_json", is_flag=True, help="Output as JSON")
def lint(file: str, use_json: bool) -> None:
    """Lint a .3mf file and report issues."""
    archive = read_3mf(file)
    config = parse_config(archive.config_bytes)

    filament_configs: dict[str, dict[str, Any]] = {}
    for path, raw in archive.get_filament_configs().items():
        filament_configs[path] = parse_config(raw)

    context = Context(config=config, filament_configs=filament_configs)

    results: list[Result] = []
    for rule_cls in RULES:
        rule = rule_cls()
        results.extend(rule.check(context))

    if use_json:
        click.echo(format_json(results))
    else:
        click.echo(format_human(results, use_color=sys.stdout.isatty()))

    # Exit code: 1 if any failures
    if any(r.severity == Severity.FAIL for r in results):
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--preset", default="bambu-to-u1", help="Preset to apply")
@click.option("--dry-run", is_flag=True, help="Show what would be fixed without applying")
@click.option("--interactive", is_flag=True, help="Prompt for each fix")
@click.option(
    "--out", "output_path", type=click.Path(), help="Output path (default: overwrite)"
)
@click.option("--json", "use_json", is_flag=True, help="Output as JSON")
@click.option(
    "--uniform-height",
    type=float,
    default=0.2,
    help="Uniform height for D1 rule (default: 0.2)",
)
def fix(
    file: str,
    preset: str,
    dry_run: bool,
    interactive: bool,
    output_path: str | None,
    use_json: bool,
    uniform_height: float,
) -> None:
    """Fix a .3mf file using a preset."""
    preset_data = _load_preset(preset)
    rules = _get_rules_for_preset(preset_data)

    # Determine fix mode
    if dry_run:
        mode = FixMode.DRY_RUN
    elif interactive:
        mode = FixMode.INTERACTIVE
    else:
        mode = FixMode.AUTO

    # Interactive callback
    interactive_callback = None
    if mode == FixMode.INTERACTIVE:
        interactive_callback = _interactive_prompt

    archive = read_3mf(file)
    config = parse_config(archive.config_bytes)

    filament_configs: dict[str, dict[str, Any]] = {}
    for path, raw in archive.get_filament_configs().items():
        filament_configs[path] = parse_config(raw)

    options: dict[str, Any] = {"uniform_height": uniform_height}

    pipeline = Pipeline(
        rules=rules,
        fixers=get_fixer_map(),
        mode=mode,
        interactive_callback=interactive_callback,
    )

    results, fixer_results, updated_config, updated_filaments = pipeline.run(
        config, filament_configs, options
    )

    if use_json:
        click.echo(format_json(results, fixer_results))
    else:
        click.echo(format_human(results, fixer_results, use_color=sys.stdout.isatty()))

    # Write output if not dry-run
    if mode != FixMode.DRY_RUN:
        archive.config_bytes = emit_config(updated_config)
        for path, fil_data in updated_filaments.items():
            archive.set_filament_config(path, emit_config(fil_data))

        out = output_path or file
        write_3mf(archive, out)

        if not use_json:
            click.echo(f"\nWritten to: {out}")


@main.group()
def presets() -> None:
    """Manage presets."""


@presets.command("list")
@click.option("--json", "use_json", is_flag=True, help="Output as JSON")
def presets_list(use_json: bool) -> None:
    """List available presets."""
    import json as json_mod

    available = _list_presets()
    if use_json:
        click.echo(json_mod.dumps(available, indent=2))
    else:
        for p in available:
            click.echo(f"  {p['name']}: {p['description']}")


def _interactive_prompt(result: Any, fixer: Any) -> bool:
    """Prompt user to accept/skip a fix in interactive mode."""
    click.echo(f"\n[{result.rule_id}] {result.message}")
    if result.diff_preview:
        click.echo(f"  Preview: {result.diff_preview}")
    return click.confirm(f"  Apply fix '{fixer.id}'?", default=True)


if __name__ == "__main__":
    main()
