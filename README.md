# CashCow - Cash Flow Modeling System

A flexible cash flow modeling system designed for rocket engine companies, featuring:
- Pure YAML files for data storage
- SQLite for efficient querying
- Flexible schema with Pydantic validation
- Plugin architecture for custom calculations
- Async/parallel processing

## Installation

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org  < /dev/null |  python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Install pre-commit hooks:
```bash
poetry run pre-commit install
```

## Usage

```bash
# Add a new employee
poetry run cashcow add --type employee

# Generate a forecast
poetry run cashcow forecast --months 24

# View KPIs
poetry run cashcow report kpi
```

## Project Structure

- `src/cashcow/` - Main application code
- `entities/` - YAML files for all entities (employees, revenues, expenses)
- `scenarios/` - Scenario definitions
- `config/` - Configuration files
- `reports/` - Generated reports
- `tests/` - Test suite
