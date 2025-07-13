# CashCow Poetry Shell Guide

## Quick Start

To run `cashcow` commands without the `poetry run` prefix:

### Method 1: Use the activation script
```bash
./activate.sh
# Then copy and run the displayed command
```

### Method 2: Direct activation
```bash
source $(poetry env info --path)/bin/activate
```

Once activated, you'll see your shell prompt change to indicate the virtual environment is active (usually with a prefix like `(cashcow-py3.13)`).

## Usage

After activation, you can run commands directly:
```bash
# Instead of: poetry run cashcow add --type employee
cashcow add --type employee

# Instead of: poetry run pytest
pytest

# Instead of: poetry run black src/
black src/
```

## Deactivation

To exit the poetry virtual environment:
```bash
deactivate
```

## Benefits

- No need to prefix commands with `poetry run`
- Faster command execution (no poetry overhead)
- Access to all installed development tools directly
- Shell prompt shows when environment is active

## Alternative: Create an Alias

If you prefer not to activate the environment, add this to your `~/.bashrc` or `~/.zshrc`:
```bash
alias cashcow='poetry run cashcow'
```

Then reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```