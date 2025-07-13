# CashCow Examples

This directory contains example configurations and use cases for the CashCow cash flow modeling system.

## Directory Structure

### basic_model/
A complete starter configuration for a startup company.

**Contents:**
- `config.yaml` - Simplified configuration file
- `entities/` - Sample entity files including:
  - `employees/founder-ceo.yaml` - Founder/CEO with equity
  - `grants/sbir-phase1.yaml` - NSF SBIR Phase I grant
  - `facilities/startup-office.yaml` - Headquarters and lab facility

**Use this when:**
- Setting up CashCow for the first time
- Learning the system with realistic examples
- Starting a new company model

### scenario_analysis/
Advanced scenario modeling for comprehensive financial planning.

**Contents:**
- `scenarios.yaml` - Multiple scenarios (baseline, conservative, optimistic, stress test)
- Monte Carlo simulation parameters
- Sensitivity analysis configurations
- What-if scenario examples

**Use this when:**
- Modeling different business outcomes
- Preparing for investor presentations
- Risk assessment and contingency planning
- Understanding sensitivity to key variables

### custom_calculations/
Examples of custom calculators for specialized business logic.

**Contents:**
- `custom_calculator.py` - Four example custom calculators:
  - Equipment testing cost calculator
  - Milestone-based contract calculator
  - Employee equity vesting calculator
  - Regulatory compliance cost calculator

**Use this when:**
- Building industry-specific calculation logic
- Implementing complex business rules
- Modeling specialized revenue or cost structures
- Extending CashCow's built-in capabilities

## Getting Started

### 1. Basic Model Setup

Copy the basic model configuration to get started quickly:

```bash
# Copy basic configuration
cp docs/examples/basic_model/config.yaml config/settings.yaml

# Copy sample entities
cp -r docs/examples/basic_model/entities/* entities/

# Generate your first forecast
poetry run cashcow forecast --months 18
```

### 2. Scenario Analysis

Set up scenario analysis for advanced planning:

```bash
# Copy scenario configurations
cp docs/examples/scenario_analysis/scenarios.yaml scenarios/

# Run different scenarios
poetry run cashcow forecast --scenario conservative --months 24
poetry run cashcow forecast --scenario optimistic --months 24
```

### 3. Custom Calculations

Implement custom business logic:

```bash
# Copy custom calculator example
cp docs/examples/custom_calculations/custom_calculator.py .

# Register calculators in your application
python custom_calculator.py
```

## Example Workflows

### Startup Launch Planning
1. Start with `basic_model/` configuration
2. Customize entity examples for your specific situation
3. Run initial forecasts to understand cash needs
4. Use `scenario_analysis/` to model different outcomes

### Investor Presentation Prep
1. Use `scenario_analysis/scenarios.yaml` for multiple scenarios
2. Generate Monte Carlo simulations for uncertainty analysis
3. Create what-if scenarios for different funding amounts
4. Export results to CSV/HTML for presentation materials

### Operational Planning
1. Use `custom_calculations/` for industry-specific costs
2. Model regulatory compliance expenses
3. Plan equipment testing campaigns
4. Track milestone-based contract revenue

## Customization Tips

### Modifying Entity Examples
- Adjust salaries and benefits to match your location/market
- Update facility costs for your specific needs
- Modify grant amounts and timelines based on actual opportunities
- Add or remove entity fields as needed (CashCow supports flexible schemas)

### Scenario Customization
- Adjust probability weights based on your risk assessment
- Modify growth rates to match your market projections
- Add industry-specific variables to sensitivity analysis
- Create scenario variants for different business strategies

### Custom Calculator Development
- Follow the patterns in `custom_calculator.py`
- Implement your own Calculator class with `calculate()` method
- Register calculators with `CalculatorRegistry.register()`
- Reference calculator names in your `config.yaml`

## Real-World Usage

These examples are based on real business scenarios:

- **Grant funding**: Based on actual government program parameters
- **Facility costs**: Realistic business corridor pricing
- **Salary ranges**: Current technology market rates
- **Testing costs**: Simplified but realistic product testing economics
- **Contract structures**: Based on actual industry contract patterns

## Next Steps

After working through these examples:

1. **Customize for your business**: Modify entities and scenarios to match your specific situation
2. **Add your own calculators**: Implement business logic specific to your operations
3. **Integrate with your tools**: Use CashCow's API to integrate with existing systems
4. **Automate reporting**: Set up scheduled forecasts and KPI monitoring
5. **Expand scenarios**: Add more sophisticated risk modeling and optimization

## Support

- See [GETTING_STARTED.md](../GETTING_STARTED.md) for basic setup instructions
- Check [TROUBLESHOOTING.md](../advanced/TROUBLESHOOTING.md) for common issues
- Review the main documentation for detailed API reference
- Join the community for questions and best practices