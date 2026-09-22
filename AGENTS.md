# AGENTS.md

## Repository Purpose

**Pyflowsheet** is a Python package for generating Process Flow Diagrams (PFD) from code using SVG drawings. Designed for chemical and process engineers, it visualizes flowsheets and unit operations modeled in textual simulators or scripts without requiring complex CAD or chart drawing software. Core features include unit operation layout, automated stream routing (via pathfinding heuristics), callouts, and optional matplotlib-based plots and tables.

## Map

Highest-level structure of key assets and documentation:

- `pyflowsheet/`: Python package source code (`core`, `unitoperations`, `backends`, `annotations`, `internals`).
- `docs/`: HTML documentation files and API reference pages.
- `examples/`: Interactive Jupyter notebooks demonstrating flowsheet features, configurations, and use cases.
- `img/`: Graphic assets, icons, and sample SVG flowsheet diagrams referenced throughout documentation.
- `readme.md` & `changelog.md`: Human-oriented project overview, guides, and version history.
- `setup.py`: Packaging and dependency configuration.

## Environment & Tooling

- Use **`uv`** for all virtual environment management and Python command execution whenever possible:
  - Create venv: `uv venv`
  - Install dependencies (editable): `uv pip install -e .`
  - Install with plot support: `uv pip install -e ".[plots]"`
  - Execute scripts: `uv run python <script.py>`
  - Run modules / commands: `uv run <command>`

## Operational Boundaries & Safety

- **Confine work to workspace**: Do not work outside the working directory. All file modifications, scratch work, and operations must remain within this repository root.
- **Protect secrets**: Never commit secrets, API keys, credentials, tokens, or environment files containing sensitive information.
- **No destructive Git commands**: Never run destructive git operations (including `git push --force`, `git reset --hard`, `git branch -D`, or aggressive `git clean`) without an explicit instruction from the user.
