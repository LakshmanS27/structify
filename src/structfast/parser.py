"""Parsing utilities for text-based folder structures."""

from __future__ import annotations

from dataclasses import dataclass

from structfast.exceptions import ParseError
from structfast.models import Node
from structfast.utils import (
    clean_node_name,
    detect_tree_depth,
    infer_type,
    is_probably_tree_line,
    load_text,
    normalize_text,
    sanitize_line,
    split_alternative_names,
    strip_tree_artifacts,
)


@dataclass(slots=True)
class _LineToken:
    raw: str
    name: str
    indent: int
    tree_depth: int | None


def parse_structure(source: str, *, smart: bool = False) -> list[Node]:
    """Parse a text structure from a raw string or path-like string into nodes."""
    text = load_text(source)
    tokens = _tokenize(text, smart=smart)
    if not tokens:
        raise ParseError("No structure entries were found in the provided input.")

    indent_levels = _build_indent_levels(tokens, smart=smart)
    nodes: list[Node] = []
    for index, token in enumerate(tokens):
        depth = token.tree_depth if token.tree_depth is not None else indent_levels[token.indent]
        next_depth: int | None = None
        if index + 1 < len(tokens):
            next_token = tokens[index + 1]
            next_depth = next_token.tree_depth if next_token.tree_depth is not None else indent_levels[next_token.indent]
        node_type = infer_type(token.name, next_depth=next_depth, current_depth=depth)
        nodes.append(Node(name=token.name.rstrip("/"), type=node_type, depth=depth))

    _validate_nodes(nodes)
    return nodes


def _tokenize(text: str, *, smart: bool) -> list[_LineToken]:
    """Convert raw text into normalized line tokens."""
    tokens: list[_LineToken] = []
    for line in normalize_text(text):
        sanitized = sanitize_line(line, smart=smart)
        if not is_probably_tree_line(sanitized):
            continue

        stripped = sanitized.lstrip(" ")
        indent = len(sanitized) - len(stripped)
        prefix_length = len(stripped) - len(stripped.lstrip("│| ├└+\\─-"))
        prefix = stripped[:prefix_length]
        name = clean_node_name(strip_tree_artifacts(stripped))
        if not name:
            continue
        tree_depth = None
        if prefix and any(char in prefix for char in "│|├└+\\"):
            tree_depth = detect_tree_depth(prefix)
            if any(marker in stripped for marker in ("├", "└", "+", "\\")):
                tree_depth += 1
        for alternative_name in split_alternative_names(name):
            tokens.append(
                _LineToken(
                    raw=sanitized,
                    name=alternative_name,
                    indent=indent,
                    tree_depth=tree_depth,
                )
            )
    return tokens


def _build_indent_levels(tokens: list[_LineToken], *, smart: bool) -> dict[int, int]:
    """Map indentation widths to hierarchy depths."""
    indents = sorted({token.indent for token in tokens})
    if not indents:
        return {0: 0}
    if smart:
        return {indent: index for index, indent in enumerate(indents)}

    positive_indents = [indent for indent in indents if indent > 0]
    if not positive_indents:
        return {0: 0}
    if min(positive_indents) > 4 and not any(token.tree_depth is not None for token in tokens):
        raise ParseError(
            "Invalid tree format: indentation jumps are too large to infer safely. "
            "Try enabling smart mode to normalize inconsistent indentation."
        )
    unit = min(positive_indents)
    levels = {0: 0}
    for indent in indents:
        levels[indent] = indent // unit
    return levels


def _validate_nodes(nodes: list[Node]) -> None:
    """Ensure parsed nodes form a sensible tree."""
    if nodes[0].depth != 0:
        raise ParseError("The structure must start at depth 0.")
    previous_depth = 0
    for node in nodes[1:]:
        if node.depth - previous_depth > 1:
            raise ParseError(
                "Invalid tree format: a node jumps more than one nesting level. "
                "Try enabling smart mode to normalize inconsistent indentation."
            )
        previous_depth = node.depth
