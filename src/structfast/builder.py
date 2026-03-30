"""Filesystem builder and export helpers."""

from __future__ import annotations

from pathlib import Path

from structfast.exceptions import BuildError
from structfast.models import BuildAction, BuildResult, Node
from structfast.parser import parse_structure
from structfast.utils import format_tree, load_text


def build_nodes(
    nodes: list[Node],
    *,
    root: str | Path = ".",
    dry_run: bool = False,
    force: bool = False,
    skip_existing: bool = False,
) -> BuildResult:
    """Create directories and files from parsed nodes."""
    root_path = Path(root).expanduser().resolve()
    root_path.mkdir(parents=True, exist_ok=True)

    result = BuildResult()
    stack: list[Path] = []

    for node in nodes:
        while len(stack) > node.depth:
            stack.pop()
        parent = stack[-1] if stack else root_path
        target = parent / node.name
        relative_path = target.relative_to(root_path)

        if node.type == "dir":
            status = _create_directory(target, dry_run=dry_run, skip_existing=skip_existing)
            result.actions.append(
                BuildAction(kind="dir", path=target, relative_path=relative_path, status=status)
            )
            if len(stack) == node.depth:
                stack.append(target)
            else:
                stack[node.depth] = target
            continue

        status = _create_file(
            target,
            dry_run=dry_run,
            force=force,
            skip_existing=skip_existing,
        )
        result.actions.append(
            BuildAction(kind="file", path=target, relative_path=relative_path, status=status)
        )

    return result


def build_structure(
    source: str | Path,
    *,
    root: str | Path = ".",
    dry_run: bool = False,
    force: bool = False,
    skip_existing: bool = False,
    smart: bool = False,
) -> BuildResult:
    """Parse a structure source and build it on disk."""
    if force and skip_existing:
        raise BuildError("The 'force' and 'skip_existing' options cannot be used together.")
    text = load_text(source)
    nodes = parse_structure(text, smart=smart)
    return build_nodes(
        nodes,
        root=root,
        dry_run=dry_run,
        force=force,
        skip_existing=skip_existing,
    )


def export_structure(path: str | Path) -> str:
    """Export an existing directory into a tree-style text structure."""
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise BuildError(f"Cannot export '{root}': path does not exist.")
    return "\n".join(format_tree(root))


def _create_directory(path: Path, *, dry_run: bool, skip_existing: bool) -> str:
    """Create a directory safely."""
    if path.exists():
        if path.is_file():
            raise BuildError(f"Cannot create directory '{path}': a file already exists at that path.")
        return "skipped" if skip_existing else "exists" if not dry_run else "planned"
    if dry_run:
        return "planned"
    path.mkdir(parents=True, exist_ok=True)
    return "created"


def _create_file(path: Path, *, dry_run: bool, force: bool, skip_existing: bool) -> str:
    """Create or overwrite a file safely."""
    if path.exists():
        if path.is_dir():
            raise BuildError(f"Cannot create file '{path}': a directory already exists at that path.")
        if skip_existing:
            return "skipped"
        if not force:
            return "exists" if not dry_run else "planned"
        if dry_run:
            return "planned"
        path.write_text("", encoding="utf-8")
        return "overwritten"
    if dry_run:
        return "planned"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    return "created"
