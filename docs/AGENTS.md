# Agent Guidelines

## Commands
- **Build**: `python -m build`
- **Lint**: `flake8 .` (max line length: 88, ignores E203, W503, E402)
- **Format**: `black .` (line length: 88)
- **Test**: `pytest tests/`
- **Single test**: `pytest tests/test_specific.py::test_function`

## Code Style
- **Imports**: Group stdlib, then third-party, then local imports (separated by blank lines)
- **Formatting**: Use black, 88 char line length
- **Types**: Use type hints for function parameters and returns
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error handling**: Use exceptions, not return codes; use sys.exit(1) for fatal errors
- **Docstrings**: Use triple quotes with Args/Returns sections for functions

## Project Structure
- Main entry: `FPLGaffer.py`
- Config: `config/` (constants, settings, environment validation)
- Models: `models/` (ratings, replacements, sorting algorithms)
- Utils: `utils/` (file handlers, date formatting, output formatting)
- AI: `ai/` (prompt engineering, AI advisor logic)
- Modes: `modes/` (transfer_mode, wildcard_mode for different FPL strategies)

## Dependencies
- Core: requests, openai, python-dotenv
- Data: pandas, numpy, scikit-learn
- Formatting: tabulate
- Dev: black, flake8, setuptools, wheel

## Testing
- Use pytest
- Test files: `tests/`
- Test naming: `test_*.py`
- Currently no test suite exists - create tests when adding new features