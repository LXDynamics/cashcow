---
title: CLI Reference
sidebar_label: CLI Reference
sidebar_position: 1
description: Comprehensive command-line interface reference for CashCow
---

# CashCow CLI Reference

A comprehensive command-line interface for cash flow modeling and financial forecasting for businesses.

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Command Overview](#command-overview)
3. [Command Reference](#command-reference)
4. [Common Workflows](#common-workflows)
5. [Configuration](#configuration)
6. [Examples](#examples)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Poetry (for dependency management)

### Installation
```bash
# Clone and install
cd /path/to/cashcow
poetry install

# Install pre-commit hooks (optional but recommended)
poetry run pre-commit install

# Verify installation
poetry run cashcow --version
```

### Initial Setup
```bash
# Create directory structure
mkdir -p entities/{revenue/{grants,investments,sales,services},expenses/{employees,facilities,operations},projects}
mkdir -p scenarios
mkdir -p config

# Create basic configuration (if not exists)
touch config/settings.yaml
```

## Command Overview

CashCow CLI provides 5 main commands:

| Command | Purpose | Usage Frequency |
|---------|---------|----------------|
| `add` | Create new entities | High |
| `list` | View existing entities | High |
| `forecast` | Generate cash flow forecasts | High |
| `kpi` | Calculate KPI metrics | Medium |
| `validate` | Validate entity files | Medium |

## Command Reference

### Global Options

```bash
cashcow --version          # Show version information
cashcow --help            # Show general help
cashcow COMMAND --help    # Show command-specific help
```

### 1. `add` - Create New Entities

Creates new financial entities with interactive or automated input.

#### Syntax
```bash
cashcow add --type TYPE --name NAME [OPTIONS]
```

#### Options
| Option | Required | Type | Description |
|--------|----------|------|-------------|
| `--type` | Yes | Choice | Entity type (see supported types below) |
| `--name` | Yes | String | Entity name |
| `--interactive`, `-i` | No | Flag | Enable interactive prompts |
| `--file`, `-f` | No | Path | Custom file path |

#### Supported Entity Types
- **employee** - Staff members with salaries and benefits
- **grant** - Government or institutional funding
- **investment** - Investor funding rounds
- **sale** - One-time revenue from customers
- **service** - Recurring revenue streams
- **facility** - Real estate and facility costs
- **software** - Software subscriptions and licenses
- **equipment** - Capital expenditures
- **project** - Project-based expenses with milestones

#### Examples

**Basic entity creation:**
```bash
# Create employee with default values
cashcow add --type employee --name "John Smith"

# Create grant with interactive prompts
cashcow add --type grant --name "NASA SBIR Phase I" --interactive

# Save to custom location
cashcow add --type facility --name "Main Office" --file "custom/path/office.yaml"
```

**Interactive prompts for employee:**
```bash
$ cashcow add --type employee --name "Jane Doe" --interactive
Creating new employee: Jane Doe
Annual salary: 95000
Position []: Senior Engineer
Department [Engineering]: Propulsion
Add equity? [y/N]: y
Equity shares [0]: 1000
Add end date? [y/N]: n
✓ Created employee 'Jane Doe' at entities/expenses/employees/jane-doe.yaml
```

#### Generated File Structure
```yaml
# entities/expenses/employees/jane-doe.yaml
type: employee
name: Jane Doe
start_date: '2025-07-11'
tags: []
salary: 95000.0
position: Senior Engineer
department: Propulsion
equity_shares: 1000
```

### 2. `list` - View Existing Entities

Lists and filters entities with various criteria.

#### Syntax
```bash
cashcow list [OPTIONS]
```

#### Options
| Option | Type | Description |
|--------|------|-------------|
| `--type` | String | Filter by entity type |
| `--active` | Flag | Show only active entities |
| `--tag` | Multiple | Filter by tags (can specify multiple) |

#### Examples

```bash
# List all entities
cashcow list

# Filter by type
cashcow list --type employee

# Show only active entities
cashcow list --active

# Filter by multiple tags
cashcow list --tag engineering --tag full-time

# Combine filters
cashcow list --type employee --active --tag senior
```

#### Sample Output
```
Found 3 entities:

• John Smith (employee) - Active
  Start: 2025-01-01
  Tags: engineering, full-time

• NASA SBIR Phase I (grant) - Active
  Start: 2025-02-01
  End: 2026-02-01
  Tags: funding, r&d

• Main Office (facility) - Active
  Start: 2025-01-01
  Tags: infrastructure
```

### 3. `forecast` - Generate Cash Flow Forecasts

Generates detailed financial forecasts with multiple output formats.

#### Syntax
```bash
cashcow forecast [OPTIONS]
```

#### Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--months` | Integer | 24 | Forecast period in months |
| `--scenario` | String | baseline | Scenario name |
| `--start-date` | Date | today | Start date (YYYY-MM-DD) |
| `--format` | Choice | table | Output format (table/csv/json) |
| `--output`, `-o` | Path | - | Output file path |
| `--kpis` | Flag | False | Include KPI analysis |

#### Examples

```bash
# Basic 24-month forecast
cashcow forecast

# 12-month forecast with KPIs
cashcow forecast --months 12 --kpis

# Export to CSV
cashcow forecast --format csv --output forecast_2025.csv

# Custom start date and scenario
cashcow forecast --start-date 2025-06-01 --scenario optimistic --months 36

# JSON output to stdout
cashcow forecast --format json --months 6
```

#### Sample Output (Table Format)
```
Generating 24-month forecast using 'baseline' scenario...

=== Cash Flow Forecast Summary ===
Period: 2025-07 to 2027-07
Total Revenue: $2,450,000.00
Total Expenses: $1,890,000.00
Net Cash Flow: $560,000.00
Final Cash Balance: $1,060,000.00

=== Monthly Breakdown (First 6 Months) ===
2025-07: Revenue $85,000, Expenses $95,000, Balance $490,000
2025-08: Revenue $92,000, Expenses $97,000, Balance $485,000
2025-09: Revenue $88,000, Expenses $99,000, Balance $474,000
2025-10: Revenue $110,000, Expenses $101,000, Balance $483,000
2025-11: Revenue $95,000, Expenses $103,000, Balance $475,000
2025-12: Revenue $125,000, Expenses $105,000, Balance $495,000
```

### 4. `kpi` - Calculate KPI Metrics

Calculates and displays key performance indicators.

#### Syntax
```bash
cashcow kpi [OPTIONS]
```

#### Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--months` | Integer | 12 | Analysis period |
| `--scenario` | String | baseline | Scenario to analyze |
| `--alerts` | Flag | False | Show alerts only |

#### Examples

```bash
# Standard KPI analysis
cashcow kpi

# 6-month analysis
cashcow kpi --months 6

# Show only alerts
cashcow kpi --alerts

# Analyze specific scenario
cashcow kpi --scenario conservative --months 18
```

#### Sample Output
```
Calculating KPIs for 12-month period...

=== KPI Analysis ===
• Runway (months): 14.2 months
• Monthly burn rate: $78,500.00
• Revenue growth rate: 8.5%
• R&D percentage: 25.3%
• Revenue per employee: $145,000.00
• Cash efficiency: 1.85

⚠ 2 alerts:
  WARNING: Runway below 18 months - consider reducing burn rate
  INFO: R&D spending above 20% - monitor for efficiency
```

### 5. `validate` - Validate Entity Files

Validates all entity YAML files for syntax and business rules.

#### Syntax
```bash
cashcow validate [OPTIONS]
```

#### Options
| Option | Type | Description |
|--------|------|-------------|
| `--fix` | Flag | Attempt to fix validation errors |

#### Examples

```bash
# Validate all files
cashcow validate

# Validate with auto-fix attempt
cashcow validate --fix
```

#### Sample Output
```
Validating entity files...
✓ john-smith.yaml
✓ nasa-sbir-phase-i.yaml
❌ main-office.yaml: 'monthly_cost' is required for facility entities
✓ server-costs.yaml

Found 1 validation errors.
Auto-fix not yet implemented.
```

## Common Workflows

### 1. Setting Up a New Project

```bash
# 1. Create directory structure
mkdir -p entities/{revenue,expenses,projects}

# 2. Add initial employees
cashcow add --type employee --name "CEO" --interactive
cashcow add --type employee --name "CTO" --interactive

# 3. Add facility costs
cashcow add --type facility --name "Office Lease" --interactive

# 4. Validate setup
cashcow validate

# 5. Generate initial forecast
cashcow forecast --months 12 --kpis
```

### 2. Monthly Financial Review

```bash
# 1. List all active entities
cashcow list --active

# 2. Generate current forecast
cashcow forecast --months 6 --format csv --output monthly_forecast.csv

# 3. Check KPIs and alerts
cashcow kpi --alerts

# 4. Full KPI analysis
cashcow kpi --months 12
```

### 3. Adding New Team Members

```bash
# 1. Add employee with full details
cashcow add --type employee --name "New Engineer" --interactive

# 2. Verify addition
cashcow list --type employee

# 3. Update forecast to see impact
cashcow forecast --months 24 --kpis

# 4. Check runway impact
cashcow kpi --alerts
```

### 4. Scenario Planning

```bash
# 1. Create baseline forecast
cashcow forecast --scenario baseline --output baseline.csv

# 2. Create scenarios (requires manual scenario files)
# Edit scenarios/optimistic.yaml with growth assumptions

# 3. Compare scenarios
cashcow forecast --scenario optimistic --output optimistic.csv
cashcow forecast --scenario conservative --output conservative.csv

# 4. Analyze KPIs for each
cashcow kpi --scenario optimistic
cashcow kpi --scenario conservative
```

## Configuration

### Entity Type Configuration (`config/settings.yaml`)

```yaml
cashcow:
  version: "1.0"
  database: cashcow.db
  
  entity_types:
    employee:
      required_fields: [salary]
      calculators: [salary_calc, equity_calc, overhead_calc]
      default_overhead_multiplier: 1.3
      
    grant:
      required_fields: [amount]
      calculators: [milestone_calc, disbursement_calc]
      
    # ... additional entity types
```

### KPI Configuration

```yaml
  kpis:
    - name: runway
      description: "Months until cash reaches zero"
      category: financial
    - name: burn_rate
      description: "Monthly cash consumption"
      category: financial
    # ... additional KPIs
```

### Reporting Configuration

```yaml
  reporting:
    default_forecast_months: 24
    chart_style: seaborn
    output_formats: [csv, json, html]
```

## Directory Structure

```
cashcow/
├── entities/
│   ├── revenue/
│   │   ├── grants/          # Grant entities
│   │   ├── investments/     # Investment entities
│   │   ├── sales/          # One-time sales
│   │   └── services/       # Recurring services
│   ├── expenses/
│   │   ├── employees/      # Employee entities
│   │   ├── facilities/     # Facility costs
│   │   └── operations/     # Software, equipment
│   └── projects/           # Project entities
├── scenarios/              # Scenario override files
├── config/
│   └── settings.yaml      # Main configuration
└── cashcow.db            # SQLite database (auto-created)
```

## Entity File Formats

### Employee Entity
```yaml
type: employee
name: John Smith
start_date: '2025-01-01'
end_date: null  # Optional
tags: [engineering, full-time]
salary: 85000
position: Software Engineer
department: Engineering
overhead_multiplier: 1.3
equity_eligible: true
equity_shares: 500
pay_frequency: monthly
benefits:
  health_insurance: 800
  dental: 100
allowances:
  phone: 100
  internet: 75
```

### Grant Entity
```yaml
type: grant
name: NASA SBIR Phase I
start_date: '2025-02-01'
end_date: '2026-02-01'
tags: [nasa, sbir, r&d]
amount: 256000
funding_agency: NASA
program: SBIR
milestones:
  - name: Initial Research
    amount: 64000
    date: '2025-05-01'
  - name: Prototype Development
    amount: 128000
    date: '2025-08-01'
  - name: Final Report
    amount: 64000
    date: '2026-02-01'
```

### Facility Entity
```yaml
type: facility
name: Main Office
start_date: '2025-01-01'
tags: [office, lease]
monthly_cost: 12000
location: Silicon Valley, CA
lease_type: Monthly
square_footage: 4000
utilities_included: false
additional_costs:
  utilities: 800
  insurance: 300
  maintenance: 200
```

## Best Practices

### 1. Entity Management
- Use descriptive names for entities
- Apply consistent tagging strategies
- Set realistic start and end dates
- Validate files regularly

### 2. Forecasting
- Generate forecasts monthly
- Use appropriate time horizons (12-36 months)
- Include KPI analysis in reviews
- Export forecasts for historical tracking

### 3. File Organization
- Follow the standard directory structure
- Use consistent naming conventions (lowercase, hyphens)
- Group related entities with tags
- Backup entity files regularly

### 4. Scenario Planning
- Create multiple scenarios (optimistic, baseline, conservative)
- Document scenario assumptions
- Compare scenarios regularly
- Update scenarios based on new information

### 5. KPI Monitoring
- Check alerts weekly
- Monitor runway closely
- Track growth metrics
- Set up thresholds for key metrics

## Examples

### Complete Project Setup Example

```bash
#!/bin/bash
# Complete CashCow setup script

echo "Setting up CashCow project..."

# 1. Create directory structure
mkdir -p entities/{revenue/{grants,investments,sales,services},expenses/{employees,facilities,operations},projects}
mkdir -p scenarios

# 2. Add core team
cashcow add --type employee --name "CEO" \
  --interactive << EOF
150000
Chief Executive Officer
Executive
n
n
EOF

cashcow add --type employee --name "CTO" \
  --interactive << EOF
140000
Chief Technology Officer
Engineering
y
2000
n
EOF

# 3. Add facility
cashcow add --type facility --name "Office Lease" \
  --interactive << EOF
8000
Palo Alto, CA
Monthly
n
EOF

# 4. Add initial grant
cashcow add --type grant --name "Seed Grant" \
  --interactive << EOF
100000
Angel Investors
Seed Round
n
EOF

# 5. Validate setup
echo "Validating entities..."
cashcow validate

# 6. Generate initial forecast
echo "Generating 18-month forecast..."
cashcow forecast --months 18 --kpis --output initial_forecast.csv

echo "Setup complete! Check initial_forecast.csv for results."
```

### Monthly Review Script

```bash
#!/bin/bash
# Monthly financial review automation

DATE=$(date +%Y-%m)
REPORT_DIR="reports/$DATE"

mkdir -p "$REPORT_DIR"

echo "Generating monthly financial review for $DATE..."

# 1. Current status
cashcow list --active > "$REPORT_DIR/active_entities.txt"

# 2. Forecasts
cashcow forecast --months 12 --format csv --output "$REPORT_DIR/forecast_12m.csv"
cashcow forecast --months 24 --format csv --output "$REPORT_DIR/forecast_24m.csv"

# 3. KPI analysis
cashcow kpi --months 12 > "$REPORT_DIR/kpi_analysis.txt"
cashcow kpi --alerts > "$REPORT_DIR/kpi_alerts.txt"

# 4. Validation
cashcow validate > "$REPORT_DIR/validation_report.txt"

echo "Monthly review complete. Reports saved to $REPORT_DIR/"
```

## Troubleshooting

### Common Issues

#### 1. "No entities directory found"
```bash
# Create the required directory structure
mkdir -p entities/{revenue,expenses,projects}
```

#### 2. "Entity validation failed"
```bash
# Check the specific error and fix the YAML file
cashcow validate

# Common issues:
# - Missing required fields
# - Invalid date formats (use YYYY-MM-DD)
# - Incorrect entity type
# - YAML syntax errors
```

#### 3. "Command not found: cashcow"
```bash
# Ensure you're using Poetry
poetry run cashcow --version

# Or activate the virtual environment
poetry shell
cashcow --version
```

#### 4. "Database errors"
```bash
# Remove and recreate the database
rm cashcow.db

# Run a forecast to recreate
cashcow forecast --months 1
```

#### 5. "Import errors"
```bash
# Reinstall dependencies
poetry install

# Check Python version
python --version  # Should be 3.10+
```

### Debug Mode

```bash
# Run with Python for detailed error messages
poetry run python -m cashcow.cli.main forecast --months 12

# Check entity loading specifically
poetry run python -c "
from cashcow.storage import EntityStore
from pathlib import Path
store = EntityStore()
store.sync_from_yaml(Path('entities'))
print(f'Loaded {len(store.entities)} entities')
"
```

### Log Files

The CLI creates log files in the working directory:
- `cashcow.log` - General application logs
- `validation.log` - Entity validation logs
- `calculation.log` - Forecast calculation logs

### Performance Issues

For large datasets:
```bash
# Use parallel calculation mode (default)
cashcow forecast --months 12

# Monitor memory usage
top -p $(pgrep -f cashcow)

# Reduce forecast period if needed
cashcow forecast --months 6
```

---

## Quick Reference Card

### Essential Commands
```bash
# Setup
mkdir -p entities/{revenue,expenses,projects}

# Add entities
cashcow add --type employee --name "Name" --interactive
cashcow add --type grant --name "Grant Name" --interactive

# Generate forecasts
cashcow forecast --months 24 --kpis
cashcow forecast --format csv --output forecast.csv

# Monitor
cashcow list --active
cashcow kpi --alerts
cashcow validate

# Export
cashcow forecast --format json --output data.json
```

### File Locations
- Entities: `entities/{revenue,expenses,projects}/`
- Config: `config/settings.yaml`
- Database: `cashcow.db`
- Scenarios: `scenarios/`

For detailed documentation and examples, visit the `/docs/examples/` directory.