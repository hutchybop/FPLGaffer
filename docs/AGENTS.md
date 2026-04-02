# Agent Guidelines for FPLGaffer

This file provides guidelines for agentic coding agents operating in this repository.

---

## Build, Lint, Test Commands

```bash
# Build package
python -m build

# Lint (flake8 configured in .flake8)
flake8 .

# Format code
black .

# Run all tests
pytest tests/

# Run single test
pytest tests/test_specific.py::test_function

# Install dev dependencies
pip install -r requirements.txt black flake8 pytest
```

Note: No test suite currently exists in `tests/`. Create tests when adding new features.

---

## Code Style Guidelines

### Imports
- Order: stdlib → third-party → local (separated by blank lines)
- Use absolute imports: `from config import constants` (not `from .config import ...`)
- Group within category, alphabetically sorted

### Formatting
- **Tool**: black
- **Line length**: 88 characters
- **Target**: Python 3.8+
- Black config in `pyproject.toml`

### Type Hints
- Use for all function parameters and return values
- Use built-in types (`list`, `dict`) or typing module (`List`, `Dict` for Python <3.9)
- Example: `def compute_ml_ratings(players: list[dict], attribute_weights: dict, mode: str = "wildcard") -> list[dict]:`

### Naming Conventions
- Variables/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private functions: prefix with `_`

### Docstrings
- Use triple quotes `"""..."""`
- Include `Args:`, `Returns:` sections for functions
- Keep brief but descriptive

### Error Handling
- Use exceptions, not return codes
- Use `sys.exit(1)` for fatal errors (e.g., missing required config)
- Use `response.raise_for_status()` for HTTP errors
- Catch specific exceptions when needed

---

## Project Structure

```
fplgaffer/
├── cli.py              # Main CLI entry point
├── web.py              # Flask web application
├── config/
│   ├── constants.py    # Global constants, API URLs, weights
│   └── settings.py     # Settings, API clients, data fetching
├── models/
│   ├── ratings.py      # ML-based player ratings
│   ├── replacements.py # Replacement suggestions logic
│   └── sort.py         # Player sorting utilities
├── utils/
│   ├── file_handlers.py # File I/O, output tee
│   ├── format_date.py   # Date formatting
│   └── print_output.py  # Console output formatting
├── ai/
│   ├── ai_prompt.py    # Prompt templates
│   └── ai_advisor.py   # AI API integration
├── modes/
│   ├── transfer_mode.py  # Transfer mode logic
│   └── wildcard_mode.py  # Wildcard mode logic
├── templates/           # HTML templates (Flask)
├── static/              # CSS/static files
└── docs/                # Documentation
```

### Key Files
- **Entry Points**: `cli.py` (CLI), `web.py` (Flask app)
- **Configuration**: `config/constants.py` (weights, URLs), `config/settings.py` (validation, API setup)
- **Core Logic**: `models/ratings.py` (rating algorithm), `modes/*.py` (strategy modes)

---

## Dependencies

### Core
- `requests` - HTTP client for FPL API
- `openai` - AI API client (Groq)
- `python-dotenv` - Environment variable loading
- `tabulate` - Table formatting

### Data Processing
- `pandas` - DataFrame operations
- `numpy` - Numerical computations
- `scikit-learn` - QuantileTransformer for ratings

### Web
- `flask` - Web framework
- `gunicorn` - WSGI server

### Development
- `black` - Code formatting
- `flake8` - Linting
- `pytest` - Testing
- `setuptools`, `wheel` - Packaging

---

## Environment Variables

Create a `.env` file based on `.env_example`:

```
FPL_TEAM_ID=YOUR_FPL_TEAM_ID
GROQ_API_KEY_FREE=YOUR_FREE_GROQ_API_KEY    # Optional
GROQ_API_KEY_PAID=YOUR_PAID_GROQ_API_KEY    # Optional
AI_MODEL=llama-3.3-70b-versatile            # Optional, default in constants.py
```

- If both Groq keys provided, free tier is used first, auto-fallback to paid
- If no keys provided, AI features are disabled

---

## Testing Guidelines

- Test files go in `tests/` directory
- Naming: `test_*.py`
- Use pytest fixtures for common setup
- Mock external APIs (FPL API, Groq) in tests
- Test both success and error paths
- Run lint/format before committing

---

## Common Patterns

### Fetching FPL Data
```python
response = requests.get(constants.BOOTSTRAP_URL)
response.raise_for_status()
data = response.json()
```

### Player Rating Computation
```python
players = ratings.compute_ml_ratings(players, weights, mode_name)
```

### AI Integration
```python
client = OpenAI(base_url=constants.BASE_URL, api_key=API_KEY)
response = client.chat.completions.create(model=model, messages=[...])
```

---

## Lint/Format Before Committing

Always run before committing:
```bash
flake8 . && black .
```

If tests exist:
```bash
pytest tests/ && flake8 . && black .
```
