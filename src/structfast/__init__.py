"""Public package interface for structfast."""

from structfast.builder import build_structure, export_structure
from structfast.models import BuildAction, BuildResult, Node
from structfast.parser import parse_structure

__all__ = [
    "BuildAction",
    "BuildResult",
    "Node",
    "build_structure",
    "export_structure",
    "parse_structure",
]

__version__ = "0.1.0"
