"""Custom exceptions used across the package."""


class StructfastError(Exception):
    """Base exception for all structfast errors."""


class ParseError(StructfastError):
    """Raised when structure input cannot be parsed safely."""


class BuildError(StructfastError):
    """Raised when the filesystem builder cannot complete an action."""


class ClipboardError(StructfastError):
    """Raised when clipboard access fails."""
