---
title: Entity System Guide
sidebar_label: Entities
sidebar_position: 2
description: Complete guide to CashCow's entity system for modeling financial components
---

# CashCow Entity System Guide

## Overview

The CashCow system is built around a flexible entity architecture that models all financial components of a business. Each entity inherits from `BaseEntity` and provides specific validation rules, calculation methods, and financial modeling capabilities.

## Entity Architecture

### Base Entity (`BaseEntity`)

All entities in the CashCow system inherit from `BaseEntity`, which provides:

- **Flexible Schema**: Accepts any additional fields via Pydantic's `extra='allow'` configuration
- **Common Fields**: Standard fields shared across all entities
- **Date Validation**: Automatic parsing and validation of date fields
- **Active Status**: Methods to determine if an entity is active on a given date

#### Common Fields

```python
class BaseEntity(BaseModel):
    # Required fields
    type: str                    # Entity type identifier
    name: str                    # Human-readable name
    start_date: date            # When entity becomes active
    
    # Optional fields
    end_date: Optional[date]    # When entity ends (None = indefinite)
    tags: List[str]             # Classification tags
    notes: Optional[str]        # Free-form notes
```

#### Core Methods

- `is_active(as_of_date)`: Check if entity is active on a specific date
- `get_field(field_name, default)`: Safely access fields with defaults
- `to_dict()`: Convert to dictionary including extra fields
- `from_yaml_dict(data)`: Create entity from YAML data

## Entity Types

### 1. Revenue Entities

#### Grant (`Grant`)
Government or institutional funding with milestone tracking.

**Required Fields:**
- `amount: float` - Total grant amount

**Key Features:**
- Milestone tracking with payment schedules
- Indirect cost rate calculations
- Agency and program tracking
- Reporting requirement management

**Example:**
```yaml
type: grant
name: Government SBIR Phase II
amount: 750000
agency: Department of Commerce
program: SBIR
start_date: 2024-01-01
end_date: 2025-12-31
milestones:
  - name: Prototype Completion
    date: 2024-06-30
    amount: 250000
    status: planned
```

**Validation Rules:**
- Amount must be positive
- Indirect cost rate between 0 and 1.0
- Milestone amounts cannot exceed total grant

#### Investment (`Investment`)
Venture capital or private investment funding.

**Required Fields:**
- `amount: float` - Investment amount

**Key Features:**
- Valuation tracking (pre/post money)
- Terms management (liquidation preference, anti-dilution)
- Disbursement scheduling
- Round tracking (seed, series A, etc.)

**Example:**
```yaml
type: investment
name: Series A Round
amount: 5000000
investor: Venture Capital Partners
round_type: series_a
pre_money_valuation: 15000000
start_date: 2024-03-01
```

#### Sale (`Sale`)
Product sales and one-time revenue.

**Required Fields:**
- `amount: float` - Sale amount

**Key Features:**
- Customer and product tracking
- Delivery date management
- Payment term handling
- Multi-payment scheduling

**Example:**
```yaml
type: sale
name: Enterprise Software Order
amount: 2500000
customer: TechCorp
product: Enterprise Platform License
quantity: 5
delivery_date: 2024-09-15
start_date: 2024-09-01
```

#### Service (`Service`)
Recurring service contracts and consulting.

**Required Fields:**
- `monthly_amount: float` - Monthly service revenue

**Key Features:**
- Hourly rate calculations
- Contract value distribution
- SLA requirement tracking
- Auto-renewal management

**Example:**
```yaml
type: service
name: Enterprise Technical Support
monthly_amount: 50000
customer: TechCorp
service_type: consulting
hourly_rate: 200
hours_per_month: 250
start_date: 2024-01-01
end_date: 2024-12-31
```

### 2. Expense Entities

#### Employee (`Employee`)
Personnel costs with comprehensive compensation modeling.

**Required Fields:**
- `salary: float` - Annual salary

**Key Features:**
- Overhead multiplier calculations
- Equity compensation tracking
- Bonus structure modeling
- Benefits and allowances
- One-time costs (signing bonus, relocation)

**Example:**
```yaml
type: employee
name: John Smith
salary: 120000
position: Senior Engineer
department: Propulsion
overhead_multiplier: 1.4
equity_eligible: true
equity_shares: 10000
start_date: 2024-02-01
```

**Validation Rules:**
- Salary must be positive
- Overhead multiplier between 1.0 and 3.0
- Bonus percentages between 0 and 1.0
- Pay frequency in ['monthly', 'biweekly', 'weekly', 'annual']

#### Facility (`Facility`)
Real estate and facility costs.

**Required Fields:**
- `monthly_cost: float` - Base monthly facility cost

**Key Features:**
- Utility cost tracking
- Lease term management
- Certification and permit costs
- Size and location tracking
- Cost per square foot calculations

**Example:**
```yaml
type: facility
name: Main Manufacturing Facility
monthly_cost: 25000
location: Hawthorne, CA
size_sqft: 15000
utilities_monthly: 3000
insurance_annual: 24000
start_date: 2024-01-01
```

#### Software (`Software`)
Software subscriptions and licenses.

**Required Fields:**
- `monthly_cost: float` - Monthly software cost

**Key Features:**
- License count tracking
- Annual cost conversion
- Renewal alert management
- Usage-based pricing
- Support and maintenance tracking

**Example:**
```yaml
type: software
name: SolidWorks Professional
monthly_cost: 2500
vendor: Dassault Systèmes
license_count: 10
annual_cost: 30000
start_date: 2024-01-01
```

#### Equipment (`Equipment`)
Capital equipment and asset purchases.

**Required Fields:**
- `cost: float` - Equipment purchase cost
- `purchase_date: date` - Date of purchase

**Key Features:**
- Depreciation calculations
- Maintenance cost tracking
- Warranty management
- Book value calculations
- Multiple depreciation methods

**Example:**
```yaml
type: equipment
name: CNC Machining Center
cost: 450000
purchase_date: 2024-03-15
vendor: Haas Automation
category: manufacturing
depreciation_years: 7
maintenance_cost_annual: 25000
start_date: 2024-03-15
```

### 3. Project Entities

#### Project (`Project`)
R&D projects with milestone and budget tracking.

**Required Fields:**
- `total_budget: float` - Total project budget

**Key Features:**
- Milestone tracking with completion rates
- Budget utilization monitoring
- Health score calculations
- Team member assignment
- Risk and dependency management

**Example:**
```yaml
type: project
name: Product Development Project
total_budget: 2000000
project_manager: Jane Doe
status: active
priority: high
start_date: 2024-01-01
planned_end_date: 2024-12-31
milestones:
  - name: Design Review
    planned_date: 2024-03-31
    status: completed
    budget: 200000
```

**Validation Rules:**
- Total budget must be positive
- Completion percentage between 0 and 100
- Status in ['planned', 'active', 'on_hold', 'completed', 'cancelled']
- Priority in ['low', 'medium', 'high', 'critical']

## Entity Relationships

### Storage Organization

Entities are organized in a hierarchical directory structure:

```
entities/
├── revenue/
│   ├── grants/
│   ├── investments/
│   ├── sales/
│   └── services/
├── expenses/
│   ├── employees/
│   ├── facilities/
│   ├── softwares/
│   └── equipments/
└── projects/
```

### Entity Dependencies

1. **Projects** can reference **Employees** as team members
2. **Equipment** may be assigned to **Employees** or **Facilities**
3. **Grant** milestones can link to **Project** deliverables
4. **Service** contracts may specify **Employee** resources

## Validation System

### Field Validation

Each entity type implements specific field validators using Pydantic:

```python
@field_validator('salary')
@classmethod
def validate_salary(cls, v: float) -> float:
    """Ensure salary is positive."""
    if v <= 0:
        raise ValueError('salary must be positive')
    return v
```

### Date Validation

Base entity provides date validation:
- Start dates are parsed from ISO format strings
- End dates must be after start dates
- Date fields support both string and date objects

### Custom Validation

Entity-specific validation includes:
- Range checks (overhead multipliers, percentages)
- Enum validation (status values, frequencies)
- Cross-field validation (milestone totals vs. budgets)

## Calculation Methods

### Cost Calculations

Each expense entity provides calculation methods:

```python
# Employee total cost calculation
def calculate_total_cost(self, as_of_date: date) -> float:
    return (
        self.calculate_base_monthly_cost() +
        self.calculate_overhead_cost(as_of_date) +
        self.calculate_allowances(as_of_date) +
        self.calculate_one_time_costs(as_of_date)
    )
```

### Revenue Recognition

Revenue entities handle timing and recognition:

```python
# Grant disbursement calculation
def calculate_monthly_disbursement(self, as_of_date: date) -> float:
    if self.payment_schedule:
        return self._calculate_scheduled_payment(as_of_date)
    return self._calculate_even_disbursement(as_of_date)
```

## Configuration Integration

Entity types are configured in `config/settings.yaml`:

```yaml
entity_types:
  employee:
    required_fields: [salary]
    calculators: [salary_calc, equity_calc, overhead_calc]
    default_overhead_multiplier: 1.3
```

This configuration drives:
- Validation requirements
- Calculator assignments
- Default value settings
- Report generation

## Usage Examples

### Creating Entities

```python
from cashcow.models import Employee, Grant, Project

# Create employee
employee = Employee(
    type="employee",
    name="Alice Johnson",
    salary=130000,
    position="Lead Developer",
    start_date=date(2024, 1, 15),
    overhead_multiplier=1.35
)

# Create grant with milestones
grant = Grant(
    type="grant",
    name="DOD STTR Phase I",
    amount=500000,
    agency="DOD",
    start_date=date(2024, 4, 1),
    end_date=date(2025, 3, 31),
    milestones=[
        {
            "name": "Preliminary Design",
            "date": date(2024, 7, 31),
            "amount": 150000,
            "status": "planned"
        }
    ]
)
```

### Cost Analysis

```python
# Calculate monthly costs
as_of_date = date(2024, 6, 1)

employee_cost = employee.calculate_total_cost(as_of_date)
grant_disbursement = grant.calculate_monthly_disbursement(as_of_date)

print(f"Employee monthly cost: ${employee_cost:,.2f}")
print(f"Grant disbursement: ${grant_disbursement:,.2f}")
```

### Health Monitoring

```python
# Project health assessment
project_health = project.get_project_health_score(as_of_date)
print(f"Project health score: {project_health['overall_score']}/100")
print(f"Budget health: {project_health['budget_health']}")
print(f"Schedule health: {project_health['schedule_health']}")
```

## Best Practices

### Entity Design

1. **Use descriptive names**: Entity names should clearly identify the item
2. **Include relevant tags**: Use tags for categorization and filtering
3. **Document assumptions**: Use notes field for important details
4. **Set realistic dates**: Ensure start/end dates reflect actual timelines

### Validation

1. **Validate early**: Use entity constructors to catch errors immediately
2. **Handle edge cases**: Consider scenarios like zero amounts, missing dates
3. **Use type hints**: Leverage Python type system for better validation

### Performance

1. **Cache calculations**: Store expensive calculations when possible
2. **Lazy loading**: Load entities on-demand for large datasets
3. **Batch operations**: Process multiple entities together for efficiency

## Troubleshooting

### Common Issues

1. **Date parsing errors**: Ensure dates are in ISO format (YYYY-MM-DD)
2. **Validation failures**: Check required fields and value ranges
3. **Missing calculations**: Verify entity has required fields for calculations
4. **File loading errors**: Check YAML syntax and file permissions

### Debugging Tips

1. Use `entity.to_dict()` to inspect all fields
2. Check `entity.is_active(date)` for activation issues
3. Validate data with `create_entity(data)` before saving
4. Review entity type mappings in configuration

This guide provides a comprehensive overview of the CashCow entity system. For specific implementation details, refer to the individual entity class documentation and the accompanying Mermaid diagrams.