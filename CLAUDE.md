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
poetry run pytest -vv                      # Verbose output
poetry run pytest --lf                     # Run last failed tests
```

### Code Quality
```bash
poetry run black src/ tests/               # Format code
poetry run ruff check src/ tests/          # Lint only
poetry run ruff check --fix src/ tests/    # Lint and fix
poetry run mypy src/                       # Type check
poetry run pre-commit run --all-files      # Run all checks
```

### Application Usage
```bash
# Entity Management
poetry run cashcow add --type employee
poetry run cashcow list --type employee
poetry run cashcow validate
poetry run cashcow update <entity_id> --field <field>=<value>
poetry run cashcow delete <entity_id>

# Financial Analysis
poetry run cashcow forecast --months 24
poetry run cashcow report kpi
poetry run cashcow report cashflow --format html
poetry run cashcow report summary --output reports/

# Advanced Analysis
poetry run cashcow analyze monte-carlo --iterations 1000
poetry run cashcow analyze what-if --scenario optimistic
poetry run cashcow analyze sensitivity --variable revenue_growth

# Scenario Management
poetry run cashcow scenario apply --name conservative
poetry run cashcow scenario create --name custom_scenario
poetry run cashcow scenario compare baseline optimistic
```

## Architecture

The system follows a modular plugin architecture:

- **src/cashcow/models/**: Pydantic models with flexible schema (BaseEntity allows extra fields)
- **src/cashcow/engine/**: Core calculations with calculator registry pattern
- **src/cashcow/storage/**: YAML files + SQLite database for data persistence
- **src/cashcow/cli/**: Click-based CLI with commands for entity management and reporting
- **src/cashcow/reports/**: HTML/CSV/JSON report generation with matplotlib charts
- **src/cashcow/analysis/**: Monte Carlo simulations and What-If analysis
- **src/cashcow/validation.py**: Entity validation system with type-specific validators
- **src/cashcow/watchers.py**: File watching for real-time validation

Key design patterns:
- Calculator Registry: Extensible calculation system in `engine/calculators/`
- Entity System: All entities inherit from BaseEntity with type-specific validators
- Async Support: Three execution modes (sync, async, parallel) in `engine/calculator.py`
- Scenario Management: Override system for different financial scenarios
- Repository Pattern: YAML files as source of truth with SQLite for efficient queries

## Important Implementation Details

1. **Entity Storage**: YAML files in `entities/` directory, organized by type:
   - `revenue/grants/`, `revenue/investments/`, `revenue/sales/`
   - `expenses/employees/`, `expenses/facilities/`, `expenses/operations/`
   - `projects/` for project-specific data

2. **Database**: SQLite (`cashcow.db`) created automatically:
   - Stores aggregated data for fast queries
   - Rebuilt from YAML files on startup
   - Used for reporting and analysis

3. **Validation**: Real-time validation with file watchers:
   - Custom validators per entity type in `models/validators.py`
   - Automatic validation on file changes
   - Clear error messages with fix suggestions

4. **Configuration**: 
   - Main config in `config/settings.yaml` defines entity types, KPIs, and reporting options
   - Scenarios in `scenarios/` directory (baseline, optimistic, conservative, cash-preservation)
   - Environment-specific overrides supported

5. **Testing**: 
   - Unit tests for models, calculators, and utilities
   - Integration tests for CLI commands and workflows
   - Performance tests for large datasets
   - Test fixtures in `tests/fixtures/`

6. **Code Style**: 
   - Black formatter with line-length 100
   - Ruff linter with extensive rules (see pyproject.toml)
   - MyPy with strict mode for type safety
   - Pre-commit hooks enforce all standards

7. **Performance Considerations**:
   - Async/parallel processing for large datasets
   - Efficient YAML parsing with caching
   - SQLite indexes for common queries
   - Lazy loading of entity data

8. **Extensibility**:
   - Custom calculators can be added to `engine/calculators/`
   - New entity types configurable in `config/settings.yaml`
   - Plugin system for report formats
   - Hook system for validation rules

## Entity YAML Field Reference

### Common Fields (All Entities)
All entities inherit from `BaseEntity` and support flexible schema (`extra='allow'`):

**Required Fields:**
- `type: str` - Entity type identifier (grant, investment, sale, service, employee, facility, software, equipment, project)
- `name: str` - Human-readable name
- `start_date: date` - When entity becomes active (YYYY-MM-DD format)

**Optional Fields:**
- `end_date: date | null` - When entity ends (null = indefinite)
- `tags: List[str]` - Classification tags for filtering (default: [])
- `notes: str | null` - Free-form documentation

### Revenue Entities

#### Grant (`type: grant`)
**Required:** `amount: float` (must be positive)

**Key Optional Fields:**
- `agency: str` - Funding agency name
- `program: str` - Grant program name  
- `grant_number: str` - Grant identifier
- `indirect_cost_rate: float` - Indirect cost rate (0.0-1.0, default: 0.0)
- `payment_schedule: List[Dict]` - Scheduled payments with date/amount pairs
- `milestones: List[Dict]` - Grant milestones with name/date/amount/status
- `reporting_requirements: str` - Reporting requirements
- `reporting_frequency: str` - Reporting frequency

**Example:**
```yaml
type: grant
name: "NASA SBIR Phase II"
start_date: "2024-01-01"
amount: 750000.0
agency: "NASA"
program: "SBIR"
payment_schedule:
  - date: "2024-01-01"
    amount: 375000.0
  - date: "2024-07-01"
    amount: 375000.0
```

#### Investment (`type: investment`)
**Required:** `amount: float` (must be positive)

**Key Optional Fields:**
- `investor: str` - Investor name
- `round_type: str` - seed, series_a, series_b, etc.
- `pre_money_valuation: float` - Pre-money valuation
- `post_money_valuation: float` - Post-money valuation
- `share_price: float` - Price per share
- `shares_issued: int` - Number of shares issued
- `liquidation_preference: float` - Liquidation preference multiplier
- `board_seats: int` - Number of board seats granted
- `disbursement_schedule: List[Dict]` - Payment schedule

#### Sale (`type: sale`)
**Required:** `amount: float` (must be positive)

**Key Optional Fields:**
- `customer: str` - Customer name
- `product: str` - Product sold
- `quantity: int` - Quantity sold
- `unit_price: float` - Price per unit
- `delivery_date: date` - Product delivery date
- `payment_terms: str` - Payment terms (net_30, net_60, etc.)
- `payment_schedule: List[Dict]` - Payment schedule

#### Service (`type: service`)
**Required:** `monthly_amount: float` (must be positive)

**Key Optional Fields:**
- `customer: str` - Customer name
- `service_type: str` - Type of service
- `hourly_rate: float` - Hourly billing rate
- `hours_per_month: float` - Expected monthly hours
- `minimum_commitment_months: int` - Minimum contract duration
- `auto_renewal: bool` - Auto-renewal enabled (default: false)

### Expense Entities

#### Employee (`type: employee`)
**Required:** `salary: float` (must be positive)

**Key Optional Fields:**
- `position: str` - Job title
- `department: str` - Department name
- `overhead_multiplier: float` - Cost multiplier (1.0-3.0, default: 1.3)
- `equity_eligible: bool` - Eligible for equity (default: false)
- `equity_shares: int` - Number of equity shares
- `equity_start_date: date` - Equity vesting start date
- `equity_cliff_months: int` - Cliff period (default: 12)
- `equity_vest_years: int` - Vesting period (default: 4)
- `bonus_performance_max: float` - Max performance bonus (% of salary)
- `signing_bonus: float` - One-time signing bonus
- `benefits_annual: float` - Annual benefits cost
- `home_office_stipend: float` - Monthly home office stipend

**Example:**
```yaml
type: employee
name: "Jane Smith"
start_date: "2024-01-01"
salary: 120000.0
position: "Senior Engineer"
department: "Engineering"
equity_eligible: true
equity_shares: 1000
bonus_performance_max: 0.15
```

#### Facility (`type: facility`)
**Required:** `monthly_cost: float` (must be positive)

**Key Optional Fields:**
- `location: str` - Facility address
- `size_sqft: int` - Size in square feet
- `facility_type: str` - office, lab, manufacturing, warehouse
- `utilities_monthly: float` - Monthly utilities cost
- `insurance_annual: float` - Annual insurance cost
- `lease_start_date: date` - Lease start date
- `lease_end_date: date` - Lease end date
- `maintenance_monthly: float` - Monthly maintenance
- `certifications: List[Dict]` - Required certifications with renewal dates

#### Software (`type: software`)
**Required:** `monthly_cost: float` (must be positive)

**Key Optional Fields:**
- `vendor: str` - Software vendor
- `license_count: int` - Number of licenses
- `annual_cost: float` - Annual cost (overrides monthly_cost)
- `contract_end_date: date` - Contract expiration
- `auto_renewal: bool` - Auto-renewal enabled (default: true)
- `per_user_cost: float` - Cost per user
- `support_included: bool` - Support included (default: true)

#### Equipment (`type: equipment`)
**Required:** `cost: float` (must be positive), `purchase_date: date`

**Key Optional Fields:**
- `vendor: str` - Equipment vendor
- `category: str` - computer, lab_equipment, manufacturing
- `depreciation_years: int` - Depreciation period
- `maintenance_cost_annual: float` - Annual maintenance cost
- `warranty_years: int` - Warranty period
- `location: str` - Equipment location
- `assigned_to: str` - Person assigned to

### Project Entity

#### Project (`type: project`)
**Required:** `total_budget: float` (must be positive)

**Key Optional Fields:**
- `project_manager: str` - Project manager name
- `status: str` - planned, active, on_hold, completed, cancelled
- `completion_percentage: float` - Completion % (0-100)
- `priority: str` - low, medium, high, critical
- `milestones: List[Dict]` - Project milestones
- `team_members: List[str]` - Team member names
- `planned_end_date: date` - Planned completion date
- `budget_categories: Dict[str, float]` - Budget breakdown by category

## Entity Validation Rules

### Financial Fields
- All monetary amounts must be positive
- Percentages must be between 0 and 1.0
- Overhead multipliers: 1.0 to 3.0 range

### Date Fields  
- ISO format: YYYY-MM-DD
- End dates must be after start dates
- Supports both string and date objects

### Entity-Specific Rules
- Employee: Salary > 0, valid equity parameters
- Grant: Indirect cost rate ≤ 1.0
- Project: Completion percentage 0-100
- Equipment: Depreciation years > 0

## Detailed Entity Documentation

For comprehensive entity documentation including complete field specifications, validation rules, calculation methods, and advanced examples, see:

- **Entity System Guide**: `cashcow-docs/docs/user-guides/ENTITIES_GUIDE.md`
- **Creation Examples**: `cashcow-docs/docs/examples/entity_creation_examples.md`
- **Example Entity Files**: `entities/` directory structure