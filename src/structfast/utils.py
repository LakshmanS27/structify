"""Utility helpers for parsing and formatting structure trees."""

from __future__ import annotations

import re
from pathlib import Path

from structfast.exceptions import ClipboardError

MARKDOWN_FENCE = "```"
TREE_PREFIX_RE = re.compile(r"^(?:[|│ ]{0,4}(?:[|│][ ]{3}|[ ]{4})|(?:[|│]?\s*))*(?:[├└+\\]?[─-]{2,}\s*)")
LEADING_BULLET_RE = re.compile(r"^(\s*)(?:[-*+]|\d+\.)\s+")
INLINE_COMMENT_RE = re.compile(r"\s+#.*$")
MARKDOWN_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
MARKDOWN_CODE_RE = re.compile(r"`(.+?)`")

KNOWN_FILE_NAMES = {
    "makefile",
    "dockerfile",
    "license",
    "readme",
    "requirements",
    "requirements.txt",
    "pipfile",
    "poetry.lock",
    "pyproject.toml",
    ".gitignore",
    ".env",
    ".env.example",
}


def load_text(source: str | Path) -> str:
    """Load raw structure text from a path-like input or return the string unchanged."""
    try:
        candidate = Path(source)
    except (TypeError, OSError):
        return str(source)
    if isinstance(source, Path):
        return candidate.read_text(encoding="utf-8")
    try:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    except OSError:
        return str(source)
    return str(source)


def normalize_text(text: str) -> list[str]:
    """Normalize line endings and strip markdown fences."""
    lines: list[str] = []
    in_fence = False
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        stripped = raw_line.strip()
        if stripped.startswith(MARKDOWN_FENCE):
            in_fence = not in_fence
            continue
        if in_fence or stripped:
            lines.append(raw_line)
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return []
    common_indent = min(len(line) - len(line.lstrip(" ")) for line in non_empty)
    if common_indent == 0:
        return lines
    return [line[common_indent:] if line.strip() else "" for line in lines]


def sanitize_line(line: str, *, smart: bool) -> str:
    """Remove common formatting artifacts while preserving indentation context."""
    line = line.expandtabs(4).rstrip()
    if smart:
        line = LEADING_BULLET_RE.sub(r"\1", line)
    return line


def detect_tree_depth(prefix: str) -> int:
    """Estimate depth from tree drawing characters in a line prefix."""
    depth = 0
    i = 0
    while i < len(prefix):
        segment = prefix[i : i + 4]
        if segment in {"│   ", "|   "}:
            depth += 1
            i += 4
            continue
        if segment == "    ":
            depth += 1
            i += 4
            continue
        if prefix[i] in {" ", "│", "|"}:
            i += 1
            continue
        break
    return depth


def strip_tree_artifacts(content: str) -> str:
    """Remove leading tree symbols from a content string."""
    content = TREE_PREFIX_RE.sub("", content, count=1)
    return content.strip()


def clean_node_name(content: str) -> str:
    """Normalize a parsed node name copied from markdown or docs."""
    content = INLINE_COMMENT_RE.sub("", content).strip()
    content = MARKDOWN_BOLD_RE.sub(r"\1", content)
    content = MARKDOWN_CODE_RE.sub(r"\1", content)
    return content


def split_alternative_names(content: str) -> list[str]:
    """Split obvious 'A or B' alternatives copied from prose into separate nodes."""
    parts = [part.strip() for part in re.split(r"\s+or\s+", content) if part.strip()]
    if len(parts) < 2:
        return [content]
    if all(_looks_like_path_fragment(part) for part in parts):
        return parts
    return [content]


def _looks_like_path_fragment(value: str) -> bool:
    """Return True when a token looks like a file or directory path fragment."""
    normalized = value.rstrip("/")
    lowered = normalized.lower()
    if not normalized or " " in normalized:
        return False
    if lowered in KNOWN_FILE_NAMES:
        return True
    if normalized.startswith("."):
        return True
    if "." in normalized:
        return True
    return value.endswith("/")


def infer_type(name: str, *, next_depth: int | None, current_depth: int) -> str:
    """Infer whether a node is a directory or file."""
    normalized = name.rstrip("/")
    lowered = normalized.lower()
    if name.endswith("/"):
        return "dir"
    if next_depth is not None and next_depth > current_depth:
        return "dir"
    if "/" in normalized or "\\" in normalized:
        return "dir"
    if lowered in KNOWN_FILE_NAMES:
        return "file"
    if normalized.startswith(".") and "." in normalized[1:]:
        return "file"
    if "." in normalized:
        return "file"
    return "dir"


def read_clipboard() -> str:
    """Read clipboard text using pyperclip and raise a friendly error when unavailable."""
    try:
        import pyperclip
    except ImportError as exc:
        raise ClipboardError("Clipboard support requires the 'pyperclip' dependency.") from exc

    try:
        text = pyperclip.paste()
    except pyperclip.PyperclipException as exc:  # type: ignore[attr-defined]
        raise ClipboardError(f"Unable to access clipboard: {exc}") from exc

    if not text or not text.strip():
        raise ClipboardError("Clipboard is empty or does not contain text.")
    return text


def is_probably_tree_line(line: str) -> bool:
    """Return True when a line likely represents a structure entry."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped in {"|", "│"}:
        return False
    if set(stripped) <= {"-", "─", " "}:
        return False
    return True


def format_tree(path: Path, prefix: str = "") -> list[str]:
    """Create a tree-style representation for an existing filesystem path."""
    label = f"{path.name}/" if path.is_dir() else path.name
    lines = [f"{prefix}{label}" if prefix else label]
    if not path.is_dir():
        return lines

    entries = sorted(
        path.iterdir(),
        key=lambda entry: (not entry.is_dir(), entry.name.lower()),
    )
    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        child_prefix = "    " if index == len(entries) - 1 else "│   "
        child_lines = format_tree(entry, prefix=f"{prefix}{child_prefix}")
        child_lines[0] = f"{prefix}{connector}{entry.name}/" if entry.is_dir() else f"{prefix}{connector}{entry.name}"
        lines.extend(child_lines)
    return lines
