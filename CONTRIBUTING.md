# Contributing to DataPilot

Thank you for your interest in contributing to DataPilot!

Contributions such as bug reports, feature suggestions, documentation improvements, and code changes are welcome.

## Development Environment

DataPilot requires:

- Python 3.12
- Node.js 24 (for frontend development)
- npm
- Ollama (for local LLM features)

Clone the repository and install backend development dependencies:

```bash
python -m pip install -e ".[dev]"
```

For frontend development:

```bash
cd frontend
npm ci
```

Configure local environment variables using `.env.example` as a reference. Do not commit `.env` or credentials.

## Development Workflow

1. Check existing code and related issues before making changes.
2. Keep changes focused and avoid unrelated refactoring.
3. Follow the existing project architecture and coding conventions.
4. Add or update tests when changing backend behavior.
5. Update documentation when changing public interfaces or project behavior.

## Code Quality

Before submitting backend changes, run:

```bash
ruff check backend
ruff format --check backend
pytest -c pyproject.toml -q
```

For frontend changes, run:

```bash
cd frontend
npx vue-tsc -b
npm run build
```

## Testing Guidelines

- Place maintained backend tests under `backend/tests/`.
- Use isolated temporary directories and databases for tests that require filesystem or database access.
- Do not use real business databases or production data in automated tests.
- Do not require external LLM services for ordinary unit tests.
- Clearly document any integration tests that require Ollama or other external services.

## Pull Requests

When submitting a pull request:

- Explain the problem and the proposed change.
- Describe the important implementation details.
- Include relevant test results.
- Mention any configuration or documentation changes.
- Keep the pull request focused on one logical change.

## Data and Security

Do not commit:

- `.env` files, API keys, passwords, or other credentials.
- SQLite databases or real business data.
- Private evaluation ground-truth data.
- Generated evaluation reports or local runtime artifacts.

Report security vulnerabilities privately according to [SECURITY.md](SECURITY.md), rather than disclosing them in public issues.

## Code of Conduct

Please communicate respectfully and constructively. Focus discussions on technical decisions, reproducible problems, and practical improvements.

Thank you for helping improve DataPilot!