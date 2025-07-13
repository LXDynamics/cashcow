---
title: Troubleshooting Guide
sidebar_label: Troubleshooting
sidebar_position: 2
description: Common issues and solutions for CashCow users
---

# CashCow Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using CashCow.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Configuration Problems](#configuration-problems)
- [Entity Validation Errors](#entity-validation-errors)
- [Calculation Errors](#calculation-errors)
- [Database Issues](#database-issues)
- [Performance Tips](#performance-tips)
- [Command Line Issues](#command-line-issues)

## Installation Issues

### Poetry Installation Problems

**Problem**: `poetry: command not found`
```bash
# Solution 1: Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Solution 2: Add to PATH (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Solution 3: Use pip (not recommended but works)
pip install poetry
```

**Problem**: Poetry uses wrong Python version
```bash
# Check current Python
poetry env info

# Use specific Python version
poetry env use python3.10
poetry env use /usr/bin/python3.10

# Recreate environment
poetry env remove python3.10
poetry install
```

### Dependency Conflicts

**Problem**: `SolverProblemError` during `poetry install`
```bash
# Solution 1: Update lockfile
poetry lock --no-update
poetry install

# Solution 2: Clear cache
poetry cache clear pypi --all
poetry install

# Solution 3: Force update
poetry update
```

**Problem**: Missing system dependencies (Linux)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev build-essential

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel

# For matplotlib on Ubuntu
sudo apt-get install python3-tk
```

### Python Version Issues

**Problem**: `This project requires Python ^3.10`
```bash
# Check Python version
python --version
python3 --version

# Install Python 3.10+ using pyenv (recommended)
curl https://pyenv.run | bash
pyenv install 3.10.12
pyenv local 3.10.12

# Or use system package manager
# Ubuntu 22.04+
sudo apt install python3.10 python3.10-venv

# macOS with Homebrew
brew install python@3.10
```

## Configuration Problems

### Missing Configuration File

**Problem**: `Config file not found: config/settings.yaml`
```bash
# Create default config directory
mkdir -p config

# Copy from example (if available)
cp docs/examples/basic_model/config.yaml config/settings.yaml

# Or create minimal config
cat > config/settings.yaml << 'EOF'
cashcow:
  version: "1.0"
  database: cashcow.db
  entity_types:
    employee:
      required_fields: [salary]
    grant:
      required_fields: [amount]
  kpis:
    - name: burn_rate
      description: "Monthly cash consumption"
      category: financial
EOF
```

### Invalid YAML Configuration

**Problem**: `yaml.scanner.ScannerError` when loading config
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"

# Common YAML issues:
# 1. Wrong indentation (use spaces, not tabs)
# 2. Missing quotes around strings with special characters
# 3. Incorrect list formatting

# Fix example:
# Wrong:
entity_types:
	employee:  # Tab instead of spaces
# Right:
entity_types:
  employee:    # Two spaces
```

### Permission Issues

**Problem**: `PermissionError: [Errno 13] Permission denied`
```bash
# Check file permissions
ls -la config/settings.yaml

# Fix permissions
chmod 644 config/settings.yaml
chmod 755 config/

# If running as wrong user
sudo chown -R $USER:$USER .
```

## Entity Validation Errors

### Schema Validation Failures

**Problem**: `ValidationError: 1 validation error for Employee`
```yaml
# Common issues and fixes:

# Issue 1: Missing required fields
# Error: Field required [type=missing, input=...]
# Solution: Add all required fields from config
type: employee
name: "John Doe"
salary: 100000  # This was missing

# Issue 2: Wrong data types
# Error: Input should be a valid number [type=float_parsing]
# Wrong:
salary: "100,000"
# Right:
salary: 100000

# Issue 3: Invalid dates
# Error: Input should be a valid date
# Wrong:
start_date: "01/15/2024"
# Right:
start_date: "2024-01-15"

# Issue 4: Negative values where not allowed
# Wrong:
salary: -50000
# Right:
salary: 50000
```

### YAML Syntax Errors

**Problem**: Entity files won't load due to YAML syntax
```bash
# Validate individual entity files
python -c "import yaml; yaml.safe_load(open('entities/expenses/employees/john-doe.yaml'))"

# Common fixes:
# 1. Quote strings with special characters
name: "John O'Connor"  # Not: name: John O'Connor

# 2. Proper list formatting
tags:
  - senior
  - engineering
# Not: tags: [senior, engineering]

# 3. Null values
end_date: null  # Or: end_date: ~
# Not: end_date: None
```

### File Path Issues

**Problem**: Entities not found in expected locations
```bash
# Check entity directory structure
find entities/ -name "*.yaml" -type f

# CashCow expects this structure:
entities/
├── expenses/
│   ├── employees/
│   ├── facilities/
│   └── operations/
├── revenue/
│   ├── grants/
│   ├── investments/
│   ├── sales/
│   └── services/
└── projects/

# Create missing directories
mkdir -p entities/{expenses/{employees,facilities,operations},revenue/{grants,investments,sales,services},projects}
```

## Calculation Errors

### Calculator Registry Issues

**Problem**: `KeyError: 'salary_calc'` - Calculator not found
```bash
# Check available calculators
poetry run python -c "
from cashcow.engine import CalculatorRegistry
print(CalculatorRegistry.list_calculators())
"

# Debug missing calculator
# 1. Check config/settings.yaml for typos in calculator names
# 2. Verify calculator is registered in engine/builtin_calculators.py
# 3. Import custom calculators if using them
```

### Numerical Calculation Errors

**Problem**: `ZeroDivisionError` or `OverflowError` in calculations
```bash
# Common causes and solutions:

# Issue 1: Division by zero in KPI calculations
# Solution: Check for zero values in denominators
# Example: revenue_per_employee when employees = 0

# Issue 2: Extremely large numbers
# Solution: Use reasonable ranges in entity definitions
# Wrong: salary: 999999999999
# Right: salary: 150000

# Issue 3: Date calculation errors
# Solution: Ensure start_date < end_date
start_date: "2024-01-01"
end_date: "2024-12-31"  # Not before start_date
```

### Scenario Loading Issues

**Problem**: `FileNotFoundError: scenarios/baseline.yaml`
```bash
# Create missing scenario file
mkdir -p scenarios

cat > scenarios/baseline.yaml << 'EOF'
name: baseline
description: "Default baseline scenario"
adjustments:
  revenue_growth_rate: 0.05
  hiring_rate: 1.0
  overhead_multiplier: 1.3
  grant_success_rate: 0.8
EOF

# Or copy from examples
cp docs/examples/scenario_analysis/scenarios.yaml scenarios/
```

## Database Issues

### SQLite Database Problems

**Problem**: `sqlite3.OperationalError: database is locked`
```bash
# Solution 1: Close other connections
# Check for other running CashCow processes
ps aux | grep cashcow
kill <process_id>

# Solution 2: Remove lock file
rm cashcow.db-wal
rm cashcow.db-shm

# Solution 3: Recreate database
rm cashcow.db
poetry run cashcow validate  # This will recreate the database
```

**Problem**: Database corruption
```bash
# Check database integrity
sqlite3 cashcow.db "PRAGMA integrity_check;"

# If corrupted, backup and recreate
mv cashcow.db cashcow.db.backup
poetry run cashcow validate  # Recreate from YAML files
```

**Problem**: Migration errors after updates
```bash
# Backup current database
cp cashcow.db cashcow.db.backup

# Force recreation
rm cashcow.db
poetry run cashcow validate
```

### Permission Issues with Database

**Problem**: Can't write to database file
```bash
# Check permissions
ls -la cashcow.db

# Fix permissions
chmod 664 cashcow.db
chgrp users cashcow.db  # If needed

# Check directory permissions
chmod 755 .
```

## Performance Tips

### Slow Forecast Generation

**Problem**: Forecasts take too long to generate

```bash
# For large numbers of entities:

# 1. Use parallel processing
poetry run cashcow forecast --months 24 --parallel

# 2. Limit entities for testing
poetry run cashcow forecast --months 12 --entities-limit 100

# 3. Use specific scenarios instead of all
poetry run cashcow forecast --scenario baseline

# 4. Reduce forecast period for testing
poetry run cashcow forecast --months 6
```

### Memory Usage Issues

**Problem**: High memory consumption

```bash
# Monitor memory usage
poetry run python -c "
import psutil
process = psutil.Process()
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# Solutions:
# 1. Process entities in batches
# 2. Use database storage instead of loading all in memory
# 3. Increase system memory or use smaller datasets for testing
```

### Large Dataset Handling

```bash
# For datasets with 1000+ entities:

# 1. Use database queries instead of loading all entities
# 2. Implement pagination in list commands
# 3. Use streaming for large reports
# 4. Consider using async processing for I/O bound operations
```

## Command Line Issues

### Command Not Found

**Problem**: `cashcow: command not found`
```bash
# Solution 1: Use poetry run
poetry run cashcow --help

# Solution 2: Activate virtual environment
poetry shell
cashcow --help

# Solution 3: Install in development mode
poetry install
```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'cashcow'`
```bash
# Solution 1: Reinstall in development mode
poetry install

# Solution 2: Check Python path
poetry run python -c "import sys; print('\n'.join(sys.path))"

# Solution 3: Verify package structure
ls -la src/cashcow/
```

### Click Command Issues

**Problem**: Invalid command arguments
```bash
# Check command help
poetry run cashcow --help
poetry run cashcow forecast --help

# Common issues:
# 1. Wrong date format
poetry run cashcow forecast --start-date 2024-01-01  # YYYY-MM-DD

# 2. Invalid choice values
poetry run cashcow add --type employee  # Use exact type names

# 3. File path issues
poetry run cashcow forecast --output /full/path/to/file.csv
```

## Getting More Help

### Debug Mode

Enable verbose logging for detailed error information:
```bash
# Set debug environment
export CASHCOW_DEBUG=1
poetry run cashcow forecast --months 12

# Or use Python logging
export PYTHONPATH=src/
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from cashcow.cli.main import cli
cli()
"
```

### Log Files

Check for log files in common locations:
```bash
# Look for log files
find . -name "*.log" -type f
find /tmp -name "*cashcow*" -type f

# Create custom logging
mkdir -p logs/
# Add logging configuration to your code
```

### Version Information

Get version information for debugging:
```bash
# CashCow version
poetry run cashcow --version

# Python version
python --version

# Poetry version
poetry --version

# All package versions
poetry show
```

### Community Support

- Check existing issues in the repository
- Search documentation for similar problems
- Create detailed bug reports with:
  - Error messages
  - Command that caused the issue
  - Environment information
  - Example data (if applicable)

### Creating Minimal Reproduction

When reporting issues:
```bash
# Create minimal test case
mkdir cashcow-debug
cd cashcow-debug

# Copy minimal config
mkdir config
echo "cashcow: {version: '1.0'}" > config/settings.yaml

# Create simple entity
mkdir -p entities/expenses/employees
cat > entities/expenses/employees/test.yaml << 'EOF'
type: employee
name: Test Employee
salary: 100000
start_date: 2024-01-01
EOF

# Test with minimal setup
poetry run cashcow forecast --months 6
```

This troubleshooting guide covers the most common issues. For complex problems, consider creating a minimal reproduction case and seeking community support.