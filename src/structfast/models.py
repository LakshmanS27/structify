"""Shared models used by the parser, builder, and CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

NodeType = Literal["file", "dir"]
ActionStatus = Literal["created", "exists", "overwritten", "skipped", "planned"]


@dataclass(slots=True)
class Node:
    """Represents a parsed item from a text structure."""

    name: str
    type: NodeType
    depth: int

    @property
    def display_name(self) -> str:
        """Return the CLI-friendly display name."""
        return f"{self.name}/" if self.type == "dir" and not self.name.endswith("/") else self.name


@dataclass(slots=True)
class BuildAction:
    """A single action emitted by the filesystem builder."""

    kind: NodeType
    path: Path
    relative_path: Path
    status: ActionStatus


@dataclass(slots=True)
class BuildResult:
    """Aggregate output from a build operation."""

    actions: list[BuildAction] = field(default_factory=list)

    @property
    def created_count(self) -> int:
        """Count filesystem objects that were newly created."""
        return sum(action.status == "created" for action in self.actions)

    @property
    def planned_count(self) -> int:
        """Count actions emitted during a dry run."""
        return sum(action.status == "planned" for action in self.actions)
