from pathlib import Path

from typer.testing import CliRunner

from structfast import cli

runner = CliRunner()


def test_build_command_dry_run(tmp_path: Path) -> None:
    source = tmp_path / "structure.txt"
    source.write_text("project/\n└── app.py\n", encoding="utf-8")
    result = runner.invoke(cli.app, ["build", str(source), "--root", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "[DIR] project/" in result.stdout
    assert "[FILE] project/app.py" in result.stdout
    assert "Dry run complete" in result.stdout


def test_export_command_writes_output(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "main.py").touch()
    output = tmp_path / "structure.txt"
    result = runner.invoke(cli.app, ["export", str(project), "--output", str(output)])
    assert result.exit_code == 0
    assert output.exists()
    assert "project/" in output.read_text(encoding="utf-8")


def test_paste_command_uses_clipboard(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "read_clipboard", lambda: "project/\n└── file.txt\n")
    result = runner.invoke(cli.app, ["paste", "--root", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "[FILE] project/file.txt" in result.stdout
