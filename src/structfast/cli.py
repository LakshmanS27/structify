"""Typer-powered command line interface for structfast."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from structfast import __version__
from structfast.builder import build_structure, export_structure
from structfast.exceptions import BuildError, ClipboardError, ParseError, StructfastError
from structfast.utils import read_clipboard

app = typer.Typer(
    help="Build directories and files from text-based folder trees.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


def _render_actions(result_actions: list, *, verbose: bool) -> None:
    """Render builder actions with rich."""
    if verbose:
        table = Table(title="Planned Actions")
        table.add_column("Type")
        table.add_column("Path")
        table.add_column("Status")
        for action in result_actions:
            label = "[DIR]" if action.kind == "dir" else "[FILE]"
            suffix = "/" if action.kind == "dir" else ""
            table.add_row(label, f"{action.relative_path.as_posix()}{suffix}", action.status)
        console.print(table)
        return

    for action in result_actions:
        label = "[DIR]" if action.kind == "dir" else "[FILE]"
        suffix = "/" if action.kind == "dir" else ""
        console.print(f"{label} {action.relative_path.as_posix()}{suffix}", markup=False)


def _handle_error(exc: StructfastError) -> None:
    """Display a friendly error and exit."""
    console.print(f"[red]Error:[/red] {exc}")
    raise typer.Exit(code=1)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        help="Show the installed version and exit.",
        is_eager=True,
    ),
) -> None:
    """Entry point callback for global options."""
    if version:
        console.print(f"structfast {__version__}")
        raise typer.Exit()


@app.command()
def build(
    source: str = typer.Argument(..., help="Path to a .txt/.md structure file or a raw structure string."),
    root: Path = typer.Option(Path("."), "--root", help="Destination root directory."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print actions without creating files."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files."),
    skip_existing: bool = typer.Option(False, "--skip-existing", help="Skip paths that already exist."),
    smart: bool = typer.Option(False, "--smart", help="Enable forgiving parsing for malformed trees."),
    verbose: bool = typer.Option(False, "--verbose", help="Show rich tabular output."),
) -> None:
    """Build a filesystem structure from text input."""
    try:
        result = build_structure(
            source,
            root=root,
            dry_run=dry_run,
            force=force,
            skip_existing=skip_existing,
            smart=smart,
        )
    except (BuildError, ParseError) as exc:
        _handle_error(exc)

    _render_actions(result.actions, verbose=verbose)
    if dry_run:
        console.print(f"[cyan]Dry run complete:[/cyan] {result.planned_count} action(s) planned.")
    else:
        console.print(f"[green]Build complete:[/green] {len(result.actions)} action(s) processed.")


@app.command()
def paste(
    root: Path = typer.Option(Path("."), "--root", help="Destination root directory."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print actions without creating files."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files."),
    skip_existing: bool = typer.Option(False, "--skip-existing", help="Skip paths that already exist."),
    smart: bool = typer.Option(False, "--smart", help="Enable forgiving parsing for malformed trees."),
    verbose: bool = typer.Option(False, "--verbose", help="Show rich tabular output."),
) -> None:
    """Read a structure from the clipboard and build it."""
    try:
        source = read_clipboard()
        result = build_structure(
            source,
            root=root,
            dry_run=dry_run,
            force=force,
            skip_existing=skip_existing,
            smart=smart,
        )
    except (ClipboardError, BuildError, ParseError) as exc:
        _handle_error(exc)

    _render_actions(result.actions, verbose=verbose)
    if dry_run:
        console.print(f"[cyan]Dry run complete:[/cyan] {result.planned_count} action(s) planned.")
    else:
        console.print(f"[green]Paste build complete:[/green] {len(result.actions)} action(s) processed.")


@app.command()
def export(
    path: Path = typer.Argument(Path("."), help="Directory to export."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write the export to a file."),
) -> None:
    """Generate a tree representation from an existing directory."""
    try:
        rendered = export_structure(path)
    except BuildError as exc:
        _handle_error(exc)

    if output is not None:
        output.write_text(rendered + "\n", encoding="utf-8")
        console.print(f"[green]Export written:[/green] {output}")
        return

    console.print(rendered)


if __name__ == "__main__":
    app()
