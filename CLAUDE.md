# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CashCow is a comprehensive cash flow modeling system for rocket engine companies. It's a Python-based financial forecasting tool with modular architecture, async capabilities, and flexible schema design.

## Key Commands

### Development Setup
```bash
poetry install
poetry run pre-commit install
```

### Running Tests
```bash
poetry run pytest                          # All tests
poetry run pytest tests/test_models.py     # Specific test file
poetry run pytest -k "employee"            # Pattern matching
poetry run pytest --cov=cashcow            # With coverage
```

### Code Quality
```bash
poetry run black src/ tests/               # Format code
poetry run ruff --fix src/ tests/          # Lint and fix
poetry run mypy src/                       # Type check
poetry run pre-commit run --all-files      # Run all checks
```

### Application Usage
```bash
poetry run cashcow add --type employee
poetry run cashcow forecast --months 24
poetry run cashcow validate
poetry run cashcow kpi
poetry run cashcow list
```

## Architecture

The system follows a modular plugin architecture:

- **src/cashcow/models/**: Pydantic models with flexible schema (BaseEntity allows extra fields)
- **src/cashcow/engine/**: Core calculations with calculator registry pattern
- **src/cashcow/storage/**: YAML files + SQLite database for data persistence
- **src/cashcow/cli/**: Click-based CLI with commands for entity management and reporting
- **src/cashcow/reports/**: HTML/CSV report generation with matplotlib charts
- **src/cashcow/analysis/**: Monte Carlo simulations and What-If analysis

Key design patterns:
- Calculator Registry: Extensible calculation system in `engine/calculators/`
- Entity System: All entities inherit from BaseEntity with type-specific validators
- Async Support: Three execution modes (sync, async, parallel) in `engine/calculator.py`
- Scenario Management: Override system for different financial scenarios

## Important Implementation Details

1. **Entity Storage**: YAML files in `entities/` directory, organized by type (revenue/, expenses/, projects/)
2. **Database**: SQLite (`cashcow.db`) created automatically, stores aggregated data
3. **Validation**: Real-time validation with file watchers, custom validators per entity type
4. **Configuration**: Main config in `config/settings.yaml` defines entity types, KPIs, and reporting options
5. **Testing**: Comprehensive test suite with unit, integration, and performance tests
6. **Code Style**: Black (line-length 100), Ruff with extensive rules, MyPy with strict mode