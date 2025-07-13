# Custom Calculator Examples

This directory contains comprehensive examples of how to create custom calculators for the CashCow financial modeling system, specifically tailored for rocket engine companies.

## Files Overview

- **`rocket_engine_calculators.py`** - Complete set of custom calculators for rocket engine companies
- **`test_rocket_calculators.py`** - Comprehensive test suite for the custom calculators
- **`README.md`** - This documentation file

## Calculator Categories

### 1. Rocket Engine Test Calculators

These calculators handle the costs associated with rocket engine testing and development:

- **`fuel_consumption_calc`** - Calculates monthly fuel costs based on test frequency and development phase
- **`test_infrastructure_calc`** - Calculates test facility and infrastructure costs
- **`total_testing_cost`** - Aggregates all testing-related costs including fuel, infrastructure, labor, and consumables

### 2. Manufacturing and Production Calculators

For calculating manufacturing line costs and production capacity:

- **`production_capacity_calc`** - Calculates production costs based on capacity utilization
- **`quality_assurance_calc`** - Calculates QA costs as a function of production volume

### 3. Research and Development Calculators

For R&D project cost modeling:

- **`research_milestone_calc`** - Calculates milestone-based R&D costs with risk adjustments
- **`prototype_development_calc`** - Calculates monthly prototype development costs

### 4. Regulatory and Compliance Calculators

For regulatory compliance and insurance costs:

- **`regulatory_compliance_calc`** - Calculates monthly regulatory compliance costs (FAA, ITAR, ISO)
- **`insurance_premium_calc`** - Calculates insurance premiums with risk-based adjustments

## Usage Examples

### Basic Calculator Usage

```python
from cashcow.engine import get_calculator_registry, CalculationContext
from cashcow.models.entities import create_entity
from datetime import date

# Import calculators to register them
from rocket_engine_calculators import *

# Create an entity
entity_data = {
    'name': 'Raptor_Engine_Test',
    'type': 'rocket_engine',
    'start_date': date(2024, 1, 1),
    'monthly_test_count': 10,
    'fuel_gallons_per_test': 1500,
    'development_phase': 'testing',
}

entity = create_entity(entity_data)

# Create calculation context
context = CalculationContext(
    as_of_date=date(2024, 6, 1),
    scenario="baseline",
    additional_params={'fuel_price_per_gallon': 5.25}
)

# Calculate specific value
registry = get_calculator_registry()
fuel_cost = registry.calculate(entity, "fuel_consumption_calc", context.to_dict())
print(f"Monthly fuel cost: ${fuel_cost:,.2f}")

# Calculate all values
all_costs = registry.calculate_all(entity, context.to_dict())
for calc_name, value in all_costs.items():
    print(f"{calc_name}: ${value:,.2f}")
```

### Integration with Cash Flow Engine

```python
from cashcow.engine import CashFlowEngine
from cashcow.storage import EntityStore
from datetime import date

# Initialize engine with custom calculators
store = EntityStore()
engine = CashFlowEngine(store)

# Add entities to store
store.save(entity)

# Calculate cash flow with custom calculators
start_date = date(2024, 1, 1)
end_date = date(2024, 12, 31)
df = engine.calculate_period(start_date, end_date, scenario="baseline")

print(df[['period', 'total_expenses', 'net_cash_flow']].head())
```

## Custom Calculator Development Guide

### 1. Calculator Function Structure

```python
@register_calculator(
    entity_type="your_entity_type",
    name="your_calculator_name",
    description="What this calculator does",
    dependencies=["other_calculator_names"]
)
def your_calculator_function(entity: BaseEntity, context: Dict[str, Any]) -> float:
    """
    Calculate something for an entity.
    
    Args:
        entity: The entity to calculate for
        context: Calculation context with date and scenario info
        
    Returns:
        Calculated value as float
    """
    # Always check if entity is active
    as_of_date = context.get('as_of_date', date.today())
    if not entity.is_active(as_of_date):
        return 0.0
    
    # Your calculation logic here
    result = 0.0
    
    return result
```

### 2. Best Practices

#### Error Handling
```python
def safe_calculator(entity: BaseEntity, context: Dict[str, Any]) -> float:
    try:
        # Get required attributes with defaults
        value1 = getattr(entity, 'attribute1', 0.0)
        value2 = context.get('parameter1', 1.0)
        
        # Safe division
        if value2 != 0:
            result = value1 / value2
        else:
            result = 0.0
            
        return result
    except Exception as e:
        print(f"Error in calculator: {e}")
        return 0.0
```

#### Context Usage
```python
def context_aware_calculator(entity: BaseEntity, context: Dict[str, Any]) -> float:
    # Standard context parameters
    as_of_date = context.get('as_of_date', date.today())
    scenario = context.get('scenario', 'baseline')
    
    # Custom context parameters
    custom_rate = context.get('custom_rate', getattr(entity, 'default_rate', 1.0))
    
    # Apply scenario adjustments
    scenario_multipliers = {
        'optimistic': 1.2,
        'baseline': 1.0,
        'conservative': 0.8,
    }
    
    multiplier = scenario_multipliers.get(scenario, 1.0)
    base_value = calculate_base_value(entity, as_of_date)
    
    return base_value * multiplier * custom_rate
```

#### Dependency Management
```python
@register_calculator(
    entity_type="complex_entity",
    name="complex_calculation",
    dependencies=["base_calc1", "base_calc2"]
)
def complex_calculator(entity: BaseEntity, context: Dict[str, Any]) -> float:
    registry = get_calculator_registry()
    
    # Use other calculators
    base1 = registry.calculate(entity, "base_calc1", context) or 0.0
    base2 = registry.calculate(entity, "base_calc2", context) or 0.0
    
    # Combine results
    return base1 + base2 + additional_logic(entity, context)
```

### 3. Testing Your Calculators

```python
import pytest
from datetime import date

def test_your_calculator():
    # Create test entity
    entity_data = {
        'name': 'Test_Entity',
        'type': 'your_type',
        'start_date': date(2024, 1, 1),
        'required_attribute': 100.0,
    }
    entity = create_entity(entity_data)
    
    # Create test context
    context = {
        'as_of_date': date(2024, 6, 1),
        'custom_parameter': 1.5,
    }
    
    # Test calculation
    registry = get_calculator_registry()
    result = registry.calculate(entity, "your_calculator_name", context)
    
    # Verify result
    expected = 150.0  # Based on your calculation logic
    assert result == expected
    
    # Test edge cases
    context['custom_parameter'] = 0
    result_zero = registry.calculate(entity, "your_calculator_name", context)
    assert result_zero == 0.0
```

## Entity Types and Required Attributes

### Rocket Engine Entities

Required attributes for `rocket_engine` entities:
- `monthly_test_count`: Number of tests per month
- `fuel_gallons_per_test`: Fuel consumption per test
- `development_phase`: 'development', 'testing', 'production', or 'maintenance'
- `test_stand_monthly_cost`: Monthly cost for test stand rental
- `test_crew_size`: Number of crew members for testing
- `test_crew_hourly_rate`: Hourly rate for test crew

Optional attributes:
- `fuel_price_per_gallon`: Fuel price (can come from context)
- `instrumentation_monthly_cost`: Monthly instrumentation costs
- `safety_systems_monthly_cost`: Monthly safety system costs
- `monthly_consumables_cost`: Monthly consumables cost
- `monthly_maintenance_cost`: Monthly maintenance cost

### Manufacturing Line Entities

Required attributes for `manufacturing_line` entities:
- `engines_per_month_capacity`: Production capacity
- `cost_per_engine_base`: Base cost per engine
- `monthly_fixed_overhead`: Fixed monthly overhead
- `variable_overhead_rate`: Variable overhead as percentage

### R&D Project Entities

Required attributes for `rd_project` entities:
- `milestones`: List of milestone dictionaries with 'planned_date', 'budget', 'risk_level'
- `monthly_material_budget`: Monthly material budget
- `complexity_level`: 'simple', 'medium', 'complex', or 'cutting_edge'

## Running the Examples

### Run All Tests
```bash
# From the custom_calculations directory
python -m pytest test_rocket_calculators.py -v

# Run specific test class
python -m pytest test_rocket_calculators.py::TestRocketEngineCalculators -v

# Run with coverage
python -m pytest test_rocket_calculators.py --cov=rocket_engine_calculators
```

### Run Calculator Example
```bash
# Run the example in rocket_engine_calculators.py
python rocket_engine_calculators.py
```

### Smoke Test
```bash
# Quick functionality test
python test_rocket_calculators.py
```

## Integration with Scenarios

Your custom calculators automatically work with the scenario system:

```python
from cashcow.engine import ScenarioManager, Scenario

# Create custom scenario
rocket_scenario = Scenario(
    name="aggressive_testing",
    description="Scenario with increased testing frequency",
    assumptions={
        'fuel_price_per_gallon': 6.00,  # Higher fuel price
    },
    entity_overrides=[
        {
            'entity_type': 'rocket_engine',
            'field': 'monthly_test_count',
            'multiplier': 1.5  # 50% more tests
        }
    ]
)

# Use with scenario manager
manager = ScenarioManager(store, engine)
manager.add_scenario(rocket_scenario)

# Calculate with custom scenario
df = manager.calculate_scenario("aggressive_testing", start_date, end_date)
```

## Performance Considerations

### Caching Results
```python
def expensive_calculator(entity: BaseEntity, context: Dict[str, Any]) -> float:
    # Use caching for expensive calculations
    cache_key = f"{entity.name}_{context.get('as_of_date')}"
    
    if cache_key in calculation_cache:
        return calculation_cache[cache_key]
    
    result = expensive_computation(entity, context)
    calculation_cache[cache_key] = result
    
    return result
```

### Parallel Execution
Your calculators automatically work with parallel execution modes:

```python
# Synchronous
df_sync = engine.calculate_period(start_date, end_date)

# Asynchronous
df_async = await engine.calculate_period_async(start_date, end_date)

# Parallel
df_parallel = engine.calculate_parallel(start_date, end_date, max_workers=4)
```

## Troubleshooting

### Common Issues

1. **Calculator Not Found**
   - Ensure you import the calculator module
   - Check that `@register_calculator` decorator is applied
   - Verify entity type matches exactly

2. **Missing Dependencies**
   - Use `registry.validate_dependencies()` to check
   - Ensure dependent calculators are registered first

3. **Calculation Errors**
   - Add try/catch blocks for robust error handling
   - Check for None values and missing attributes
   - Use `getattr()` with default values

4. **Performance Issues**
   - Profile your calculator functions
   - Consider caching expensive operations
   - Minimize external API calls

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints to your calculators
def debug_calculator(entity: BaseEntity, context: Dict[str, Any]) -> float:
    print(f"Calculating for {entity.name} at {context.get('as_of_date')}")
    result = your_calculation_logic(entity, context)
    print(f"Result: {result}")
    return result
```

This comprehensive example system demonstrates how to extend CashCow with domain-specific calculators while maintaining the flexibility and robustness of the core calculation engine.