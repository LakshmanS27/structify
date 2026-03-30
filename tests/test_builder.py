from pathlib import Path

import pytest

from structfast.builder import build_nodes, build_structure, export_structure
from structfast.exceptions import BuildError
from structfast.models import Node


def test_build_nodes_creates_nested_files(tmp_path: Path) -> None:
    nodes = [
        Node(name="project", type="dir", depth=0),
        Node(name="src", type="dir", depth=1),
        Node(name="main.py", type="file", depth=2),
        Node(name="README.md", type="file", depth=1),
    ]
    result = build_nodes(nodes, root=tmp_path)
    assert (tmp_path / "project" / "src" / "main.py").exists()
    assert (tmp_path / "project" / "README.md").exists()
    assert result.created_count == 4


def test_build_structure_dry_run_does_not_write(tmp_path: Path) -> None:
    result = build_structure("project/\n└── main.py\n", root=tmp_path, dry_run=True)
    assert result.planned_count == 2
    assert not (tmp_path / "project").exists()


def test_build_structure_skip_existing(tmp_path: Path) -> None:
    existing = tmp_path / "project"
    existing.mkdir()
    main_file = existing / "main.py"
    main_file.write_text("content", encoding="utf-8")

    result = build_structure(
        "project/\n└── main.py\n",
        root=tmp_path,
        skip_existing=True,
    )
    statuses = [action.status for action in result.actions]
    assert statuses == ["skipped", "skipped"]
    assert main_file.read_text(encoding="utf-8") == "content"


def test_build_structure_force_and_skip_existing_conflict(tmp_path: Path) -> None:
    with pytest.raises(BuildError):
        build_structure("root/\n└── file.txt\n", root=tmp_path, force=True, skip_existing=True)


def test_export_structure(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.py").touch()
    (project / "README.md").touch()
    exported = export_structure(project)
    assert "project/" in exported
    assert "src/" in exported
    assert "main.py" in exported
