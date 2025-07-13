---
title: Entity System Summary
sidebar_label: Entity System
sidebar_position: 3
description: Summary of CashCow's entity system architecture and implementation
---

# CashCow Entity System Summary

## Overview

The CashCow entity system provides a comprehensive framework for modeling all financial components of a business. This document summarizes the key findings from analyzing the complete entity architecture.

## Documentation Structure

This documentation package includes:

1. **[ENTITIES_GUIDE.md](../user-guides/ENTITIES_GUIDE.md)** - Comprehensive guide to all entity types
2. **[diagrams/entities/](../diagrams/entities/)** - Mermaid diagrams showing system architecture
3. **[examples/entity_creation_examples.md](examples/entity_creation_examples.md)** - Practical usage examples

## Entity Type Summary

### Revenue Entities (4 types)
| Entity | Purpose | Key Features | Required Fields |
|--------|---------|--------------|-----------------|
| **Grant** | Government/institutional funding | Milestone tracking, payment schedules | `amount` |
| **Investment** | VC/private investment | Valuation tracking, disbursement scheduling | `amount` |
| **Sale** | Product sales | Customer/product tracking, delivery management | `amount` |
| **Service** | Recurring contracts | Hourly rates, SLA management | `monthly_amount` |

### Expense Entities (4 types)
| Entity | Purpose | Key Features | Required Fields |
|--------|---------|--------------|-----------------|
| **Employee** | Personnel costs | Equity tracking, overhead calculations | `salary` |
| **Facility** | Real estate costs | Utilities, lease management | `monthly_cost` |
| **Software** | Software subscriptions | License management, renewal alerts | `monthly_cost` |
| **Equipment** | Capital equipment | Depreciation, maintenance tracking | `cost`, `purchase_date` |

### Project Entities (1 type)
| Entity | Purpose | Key Features | Required Fields |
|--------|---------|--------------|-----------------|
| **Project** | R&D projects | Milestone tracking, budget monitoring | `total_budget` |

## Architecture Highlights

### Flexible Schema Design
- **BaseEntity** foundation with `extra='allow'` configuration
- All entities inherit common fields (`type`, `name`, `start_date`, etc.)
- Custom fields supported for entity-specific requirements
- Automatic date parsing from ISO strings

### Comprehensive Validation
- **Field-level validation** using Pydantic validators
- **Cross-field validation** for logical consistency
- **Entity-specific rules** for business logic
- **Range checking** for numeric values
- **Enum validation** for status and frequency fields

### Dual Storage System
- **YAML files** as human-readable source of truth
- **SQLite database** for optimized queries and aggregations
- Organized directory structure by entity type
- Automatic file path generation from entity names

### Calculation Methods
Each entity provides specialized calculation methods:
- **Employee**: Total cost including overhead, equity, bonuses
- **Grant**: Monthly disbursements based on schedules or milestones
- **Investment**: Disbursement tracking with valuation data
- **Facility**: Total monthly cost including utilities and insurance
- **Equipment**: Depreciation and maintenance calculations
- **Project**: Burn rate and health score monitoring

## Key Design Patterns

### 1. Entity Factory Pattern
```python
def create_entity(data: Dict[str, Any]) -> BaseEntity:
    """Create appropriate entity type from dictionary."""
    entity_type = data.get('type', '').lower()
    if entity_type in ENTITY_TYPES:
        return ENTITY_TYPES[entity_type](**data)
    return BaseEntity(**data)  # Fallback for unknown types
```

### 2. Configuration-Driven Validation
Entity types are configured in `settings.yaml` with:
- Required field specifications
- Calculator assignments
- Default values and multipliers
- Validation rules

### 3. Activity-Based Calculations
All entities support activity checking:
```python
def is_active(self, as_of_date: date) -> bool:
    """Check if entity is active on given date."""
    if self.start_date > as_of_date:
        return False
    if self.end_date is None:
        return True
    return self.end_date >= as_of_date
```

### 4. Extensible Field System
Entities can have additional fields beyond the base schema:
```python
# Custom fields are automatically preserved
entity = Employee(
    name="John Doe",
    salary=100000,
    start_date=date.today(),
    custom_department_code="ENG-001",  # Custom field
    special_clearance_level="SECRET"    # Custom field
)
```

## Storage Organization

### Directory Structure
```
entities/
├── revenue/
│   ├── grants/          # Government funding
│   ├── investments/     # VC/private funding
│   ├── sales/          # Product sales
│   └── services/       # Service contracts
├── expenses/
│   ├── employees/      # Personnel
│   ├── facilities/     # Real estate
│   ├── softwares/      # Software subscriptions
│   └── equipments/     # Capital equipment
└── projects/           # R&D projects
```

### Database Schema
- **entities** table: Core entity data with JSON storage
- **metadata** table: Entity metadata and tags
- **calculations** table: Cached calculation results
- **audit_log** table: Change tracking and history

## Validation Rules Summary

### Common Validations
- **Dates**: Start date required, end date must be after start date
- **Names**: Required string fields, no empty values
- **Types**: Must match configured entity types

### Entity-Specific Validations

#### Employee
- Salary > 0
- Overhead multiplier: 1.0 - 3.0
- Bonus percentages: 0 - 1.0
- Pay frequency: ['monthly', 'biweekly', 'weekly', 'annual']

#### Grant
- Amount > 0
- Indirect cost rate: 0 - 1.0
- Milestone amounts ≤ total grant amount

#### Investment
- Amount > 0
- Valuation data consistency checks

#### Equipment
- Cost > 0
- Depreciation method: ['straight_line', 'declining_balance', 'sum_of_years']
- Maintenance percentage: 0 - 1.0

#### Project
- Total budget > 0
- Completion percentage: 0 - 100
- Status: ['planned', 'active', 'on_hold', 'completed', 'cancelled']

## Usage Best Practices

### Entity Creation
1. **Use descriptive names** for easy identification
2. **Include relevant tags** for categorization
3. **Set realistic dates** for accurate modeling
4. **Document assumptions** in notes field

### Performance Optimization
1. **Load entities on-demand** for large datasets
2. **Cache calculation results** when possible
3. **Use database queries** for complex filtering
4. **Batch operations** for multiple entities

### Data Management
1. **Validate early** to catch errors immediately
2. **Use version control** for YAML files
3. **Backup regularly** both files and database
4. **Monitor file changes** with watchers

## Integration Points

### Calculator Registry
Entities integrate with the calculator system:
- Each entity type has assigned calculators in configuration
- Calculators use entity methods for cost/revenue calculations
- Results are cached in the database for performance

### Reporting System
Entities feed into reports through:
- Aggregated cost and revenue calculations
- KPI metric generation
- Forecast modeling
- Health score monitoring

### Scenario Analysis
Entities support scenario modeling:
- Override values for what-if analysis
- Monte Carlo simulation inputs
- Sensitivity analysis parameters
- Risk assessment factors

## Error Handling

### Validation Errors
- **Detailed error messages** with field names and constraints
- **Partial loading** continues with other entities if one fails
- **Error logging** for debugging and monitoring
- **Graceful fallbacks** to BaseEntity for unknown types

### File System Errors
- **Permission checking** before file operations
- **Path validation** for directory structure
- **Atomic writes** to prevent corruption
- **Backup creation** before modifications

## Future Extensibility

### Adding New Entity Types
1. Create new entity class inheriting from BaseEntity
2. Add validation rules and calculation methods
3. Update ENTITY_TYPES mapping
4. Configure in settings.yaml
5. Add to storage directory structure

### Custom Validation Rules
1. Add field validators using Pydantic decorators
2. Implement cross-field validation methods
3. Add business rule validation
4. Test thoroughly with edge cases

### Enhanced Calculations
1. Add new calculation methods to entity classes
2. Integrate with calculator registry
3. Cache results in database
4. Update reporting system

This entity system provides a robust foundation for financial modeling in the CashCow system, with flexibility for future enhancements and comprehensive validation to ensure data integrity.