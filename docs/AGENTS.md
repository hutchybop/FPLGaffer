# FPLGaffer - Agent Development Guide

## Build/Lint/Test Commands

```bash
# Format code with Black
black .

# Lint code with Flake8
flake8 .

# Install dependencies
pip install -r requirements.txt

# Run the main application
python3 FPLGaffer.py
```

## Code Style Guidelines

### Formatting
- Line length: 88 characters (Black default)
- Target Python version: 3.8+
- Use Black for auto-formatting

### Import Organization
1. Standard library imports
2. Third-party imports (pandas, numpy, requests, openai, etc.)
3. Local imports (from config, models, utils, ai, modes)

### Naming Conventions
- Variables and functions: `snake_case`
- Constants: `UPPER_CASE` 
- Classes: `PascalCase`
- Files: `snake_case.py`

### Code Structure
- Use docstrings with triple quotes for functions
- Error handling with try/except blocks
- Environment variables via python-dotenv
- Data processing with pandas/numpy
- API calls with requests library

### Key Patterns
- ML scaling with sklearn.preprocessing.QuantileTransformer
- Tabular output with tabulate library
- File I/O with custom Tee class for dual output
- AI integration via OpenAI client (Groq API)

### Excluded Directories
- .git, __pycache__, .venv, build, dist, test_runs, reports, gaffer
