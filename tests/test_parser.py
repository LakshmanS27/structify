from pathlib import Path

import pytest

from structfast.exceptions import ParseError
from structfast.parser import parse_structure


def test_parse_unicode_tree() -> None:
    text = """
    a2a-system/
    ├── backend/
    │   ├── agents/
    │   │   ├── planner.py
    │   │   └── worker.py
    │   └── main.py
    └── requirements.txt
    """
    nodes = parse_structure(text)
    assert [(node.name, node.type, node.depth) for node in nodes] == [
        ("a2a-system", "dir", 0),
        ("backend", "dir", 1),
        ("agents", "dir", 2),
        ("planner.py", "file", 3),
        ("worker.py", "file", 3),
        ("main.py", "file", 2),
        ("requirements.txt", "file", 1),
    ]


def test_parse_indentation_based_tree() -> None:
    text = """
    project
        src
            main.py
        README.md
    """
    nodes = parse_structure(text)
    assert [node.depth for node in nodes] == [0, 1, 2, 1]
    assert [node.type for node in nodes] == ["dir", "dir", "file", "file"]


def test_parse_smart_mode_handles_markdown_and_tabs() -> None:
    text = """
    ```text
    project/
    \t- app/
    \t  - __init__.py
    \t  - service.py
    ```
    """
    nodes = parse_structure(text, smart=True)
    assert [(node.name, node.depth) for node in nodes] == [
        ("project", 0),
        ("app", 1),
        ("__init__.py", 2),
        ("service.py", 2),
    ]


def test_parse_invalid_depth_jump_raises() -> None:
    text = """
    root/
            deep.py
    """
    with pytest.raises(ParseError):
        parse_structure(text)


def test_parse_from_file_path(tmp_path: Path) -> None:
    source = tmp_path / "structure.txt"
    source.write_text("root/\n└── file.txt\n", encoding="utf-8")
    nodes = parse_structure(str(source))
    assert nodes[-1].name == "file.txt"


def test_parse_strips_markdown_wrappers_and_inline_comments() -> None:
    text = """
    project1/
    ├── **.env**                       # Environment variables
    ├── **alembic/**                   # Database migrations
    │   ├── versions/
    │   └── env.py
    ├── **app/**
    """
    nodes = parse_structure(text)
    assert [(node.name, node.type, node.depth) for node in nodes] == [
        ("project1", "dir", 0),
        (".env", "file", 1),
        ("alembic", "dir", 1),
        ("versions", "dir", 2),
        ("env.py", "file", 2),
        ("app", "dir", 1),
    ]


def test_parse_handles_partial_markdown_and_or_alternatives() -> None:
    text = """
    project1/
    ├── **__init__**.py
    ├── **requirements.txt** or **pyproject.toml** # Project dependencies/metadata
    └── **data_analyzer_agent/** # Another example agent
    """
    nodes = parse_structure(text)
    assert [(node.name, node.type, node.depth) for node in nodes] == [
        ("project1", "dir", 0),
        ("__init__.py", "file", 1),
        ("requirements.txt", "file", 1),
        ("pyproject.toml", "file", 1),
        ("data_analyzer_agent", "dir", 1),
    ]
