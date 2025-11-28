# FPLGaffer – Agent Guide

## Build / Lint / Test
```bash
# Install dependencies
pip install -r requirements.txt

# Format & lint
black .          # auto‑format (line‑length 88)
flake8 .         # PEP‑8 checks
mypy .           # optional static typing

# Run the application
python3 FPLGaffer.py

# Tests (pytest preferred)
pytest           # all tests
pytest -k <test_name>  # run a single test matching <test_name>
```

## Code Style
- **Imports**: std lib → third‑party → local, blank line between groups, alphabetic order.
- **Formatting**: Black (default settings). No trailing whitespace.
- **Naming**: `snake_case` for vars/functions, `UPPER_CASE` for constants, `PascalCase` for classes, files in `snake_case.py`.
- **Types**: Add type hints on public APIs; use `typing` for collections.
- **Docstrings**: Triple‑quoted, Google style, include Args/Returns.
- **Error handling**: Wrap external I/O/API in `try/except`, log with `logging`, raise custom exceptions when needed.
- **Logging**: Module‑level `logger = logging.getLogger(__name__)`.
- **Testing**: Place tests under `tests/`, name `test_*.py`, use pytest fixtures.

## Agent Rules
No `.cursor/` or `.github/copilot‑instructions.md` files are present, so there are no additional cursor or Copilot rules.
