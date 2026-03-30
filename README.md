# structfast

`structfast` is a production-ready Python package and CLI that turns text-based folder trees into real directories and files.

It is designed for trees copied from:

- ChatGPT or other AI tools
- GitHub READMEs
- markdown docs
- plain text notes
- indentation-only outlines

## Features

- Parse `.txt`, `.md`, or raw string input
- Support Unicode tree drawings like `├──`, `└──`, `│`
- Handle indentation-based and messy AI-generated structures
- Build safely with dry-run, overwrite, and skip-existing modes
- Read structures directly from the clipboard
- Export an existing directory back into a tree representation
- Use as both a CLI tool and a Python API

## Installation

Install with `pip`:

```bash
pip install structfast
```

Install with `uv`:

```bash
uv tool install structfast
```

Run without installing globally:

```bash
uvx structfast build structure.txt
```

## Quick Start

Given a text file named `structure.txt`:

```text
a2a-system/
├── backend/
│   ├── agents/
│   │   ├── planner.py
│   │   ├── worker.py
│   │   └── critic.py
│   └── main.py
└── requirements.txt
```

Build it in the current directory:

```bash
structfast build structure.txt
```

With `uv`:

```bash
uvx structfast build structure.txt
```

Preview without writing:

```bash
structfast build structure.txt --dry-run
```

Build into a specific root:

```bash
structfast build structure.txt --root ./sandbox
```

Paste directly from the clipboard:

```bash
structfast paste --dry-run --smart
```

Export an existing directory:

```bash
structfast export .
```

## CLI Reference

### `structfast build <source>`

Options:

- `--root PATH`: destination root directory, defaults to the current directory
- `--dry-run`: print planned actions without creating files or folders
- `--force`: overwrite existing files
- `--skip-existing`: skip any path that already exists
- `--smart`: enable aggressive cleanup for malformed trees and inconsistent indentation
- `--verbose`: show extra parser and builder details

Example output:

```text
[DIR] a2a-system/
[DIR] a2a-system/backend/
[FILE] a2a-system/backend/main.py
[FILE] a2a-system/requirements.txt
```

### `structfast paste`

Reads clipboard content using `pyperclip`, parses it, and builds the structure with the same flags as `build`.

### `structfast export <path>`

Generates a tree view from an existing directory. By default it prints to stdout; use `--output structure.txt` to write it to a file.

## Python API

```python
from structfast import build_structure, export_structure, parse_structure

result = build_structure("structure.txt", root=".", dry_run=True, smart=True)
for action in result.actions:
    print(action.kind, action.relative_path, action.status)

nodes = parse_structure(\"\"\"
project/
  app/
    main.py
  README.md
\"\"\")

tree = export_structure(".")
print(tree)
```

## Smart Parsing

The `--smart` mode makes parsing more forgiving by:

- stripping markdown fences and list bullets
- normalizing tabs to spaces
- tolerating inconsistent indentation levels
- cleaning common AI formatting artifacts
- inferring directory types from nesting when trailing `/` is missing

## Safety Model

- Existing directories are reused safely
- Existing files are only overwritten with `--force`
- Use `--skip-existing` to ignore existing paths
- Use `--dry-run` to inspect planned actions before writing

## Development

Create a local dev environment with `pip`:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Create a local dev environment with `uv`:

```bash
uv sync --dev
```

Run tests with `pip`/venv:

```bash
pytest
```

Run tests with `uv`:

```bash
uv run pytest
```

Run the CLI in development with `uv`:

```bash
uv run structfast build structure.txt --dry-run
```

Build distributions with either tool:

```bash
python -m build
```

```bash
uv build
```

## License

MIT License
