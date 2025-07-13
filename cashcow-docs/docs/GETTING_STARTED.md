---
title: Getting Started
sidebar_label: Getting Started
sidebar_position: 1
description: Installation, setup, and creating your first CashCow financial forecast
---

# Getting Started with CashCow

Welcome to CashCow, a comprehensive cash flow modeling system for businesses. This guide will walk you through installation, setup, and creating your first financial forecast.

## Prerequisites

Before installing CashCow, ensure you have the following:

- **Python 3.10 or higher**: Check with `python --version` or `python3 --version`
- **Poetry**: Python dependency management tool
- **Git**: For version control (optional but recommended)
- **SQLite3**: Usually comes pre-installed with Python

### Installing Poetry

If you don't have Poetry installed:

```bash
# On Linux/macOS/WSL:
curl -sSL https://install.python-poetry.org | python3 -

# On Windows (PowerShell):
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Add Poetry to your PATH (Linux/macOS):
export PATH="$HOME/.local/bin:$PATH"
```

## Installation

### 1. Clone the Repository (if applicable)

```bash
git clone <repository-url>
cd cashcow
```

### 2. Install Dependencies

```bash
# Install all dependencies
poetry install

# This will create a virtual environment and install:
# - Core dependencies (pydantic, pandas, matplotlib, etc.)
# - Development tools (pytest, black, mypy, etc.)
```

### 3. Activate the Virtual Environment

```bash
# Option 1: Use poetry shell
poetry shell

# Option 2: Run commands with poetry run prefix
poetry run cashcow --help
```

### 4. Set Up Pre-commit Hooks (for developers)

```bash
poetry run pre-commit install
```

## Environment Configuration

CashCow uses a configuration file located at `config/settings.yaml`. The default configuration works out of the box, but you can customize:

- Entity types and their required fields
- KPI definitions
- Default forecast parameters
- Report formats

## Your First Cash Flow Model Tutorial

Let's create a simple cash flow model for a startup company.

### Step 1: Create Your First Employee

Start by adding a founding employee:

```bash
# Interactive mode (recommended for first time)
poetry run cashcow add --type employee --name "John Doe" --interactive

# Or use defaults
poetry run cashcow add --type employee --name "John Doe"
```

In interactive mode, you'll be prompted for:
- Salary
- Start date
- Department
- Benefits
- Equity details

The entity will be saved to `entities/expenses/employees/john-doe.yaml`

### Step 2: Add Revenue Sources

#### Add a Grant
```bash
poetry run cashcow add --type grant --name "NSF SBIR Phase I" --interactive
```

Example responses:
- Amount: $275,000
- Start date: Today's date
- Disbursement schedule: 3 milestones
- Duration: 9 months

#### Add an Investment
```bash
poetry run cashcow add --type investment --name "Seed Round" --interactive
```

Example responses:
- Amount: $2,000,000
- Disbursement: Immediate
- Investor: Generic Ventures

### Step 3: Set Up Operating Expenses

#### Add Facility Costs
```bash
poetry run cashcow add --type facility --name "Main Office" --interactive
```

Example responses:
- Monthly cost: $15,000
- Location: Los Angeles
- Size: 5,000 sq ft

#### Add Software Subscriptions
```bash
poetry run cashcow add --type software --name "CAD Software Suite" --interactive
```

Example responses:
- Monthly cost: $5,000
- Number of licenses: 10

### Step 4: Generate Your First Forecast

Now let's generate a 24-month cash flow forecast:

```bash
# Basic forecast
poetry run cashcow forecast --months 24

# With KPIs
poetry run cashcow forecast --months 24 --kpis

# Save to file
poetry run cashcow forecast --months 24 --format csv --output forecast.csv

# Different scenario
poetry run cashcow forecast --months 24 --scenario conservative
```

### Step 5: View and Validate Entities

```bash
# List all entities
poetry run cashcow list

# Validate all entities
poetry run cashcow validate

# Calculate current KPIs
poetry run cashcow kpi
```

## Understanding the Output

### Forecast Output

The forecast command generates a month-by-month projection showing:

1. **Revenue Streams**
   - Grants (milestone-based disbursements)
   - Investments (lump sum or scheduled)
   - Sales revenue
   - Service contracts

2. **Expenses**
   - Personnel costs (salary + benefits + overhead)
   - Facility costs
   - Equipment and software
   - Project-specific expenses

3. **Cash Flow Summary**
   - Starting cash
   - Total revenue
   - Total expenses
   - Net cash flow
   - Ending cash balance

### Key Performance Indicators (KPIs)

When using the `--kpis` flag, you'll see:

- **Runway**: Months until cash reaches zero
- **Burn Rate**: Monthly cash consumption
- **Revenue Growth**: Month-over-month percentage
- **R&D Percentage**: R&D spend as % of total expenses
- **Revenue per Employee**: Efficiency metric
- **Customer Acquisition Cost (CAC)**: If applicable

### Example Output

```
Cash Flow Forecast (24 months)
================================

Month    Revenue    Expenses    Net Flow    Cash Balance
2024-01  $250,000   $45,000    $205,000    $205,000
2024-02  $50,000    $45,000    $5,000      $210,000
2024-03  $50,000    $52,000    -$2,000     $208,000
...

Key Metrics:
- Current Runway: 18.5 months
- Average Burn Rate: $48,500/month
- Revenue Growth: 15% MoM
```

## Directory Structure

After setting up your model, your directory structure will look like:

```
cashcow/
├── config/
│   └── settings.yaml          # Main configuration
├── entities/
│   ├── expenses/
│   │   ├── employees/         # Employee YAML files
│   │   ├── facilities/        # Office/lab costs
│   │   └── operations/        # Other operating expenses
│   ├── revenue/
│   │   ├── grants/           # Grant funding
│   │   ├── investments/      # VC/angel investments
│   │   ├── sales/           # Product sales
│   │   └── services/        # Service contracts
│   └── projects/            # R&D projects
├── scenarios/               # Different forecast scenarios
├── reports/                # Generated reports
└── cashcow.db             # SQLite database (auto-created)
```

## Next Steps

1. **Explore Scenarios**: Create different scenarios (optimistic, conservative) in the `scenarios/` directory
2. **Custom Calculations**: Add custom calculators for specialized business logic
3. **Automated Reports**: Set up scheduled reports using the reporting module
4. **Monte Carlo Analysis**: Use the analysis module for uncertainty modeling
5. **API Integration**: Integrate CashCow with your existing tools

### Advanced Features to Explore

- **Scenario Analysis**: Model different business outcomes
- **What-If Analysis**: Test sensitivity to key variables
- **Custom KPIs**: Define metrics specific to your business
- **Batch Operations**: Import/export multiple entities
- **Real-time Validation**: File watchers for instant feedback

## Getting Help

- Check the [Troubleshooting Guide](advanced/TROUBLESHOOTING.md) for common issues
- Review example configurations in `docs/examples/`
- Run `poetry run cashcow --help` for command reference
- Each command has its own help: `poetry run cashcow forecast --help`

## Quick Command Reference

```bash
# Entity Management
poetry run cashcow add --type <type> --name <name>
poetry run cashcow list [--type <type>]
poetry run cashcow validate

# Forecasting
poetry run cashcow forecast [--months N] [--scenario NAME]
poetry run cashcow kpi

# Development
poetry run pytest                    # Run tests
poetry run black src/ tests/         # Format code
poetry run mypy src/                 # Type check
```

Welcome to CashCow! Start with a simple model and gradually add complexity as your business grows.