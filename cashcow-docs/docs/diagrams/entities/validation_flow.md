# Entity Validation Flow

```mermaid
flowchart TB
    Start([Entity Creation]) --> LoadData{Data Source}
    
    LoadData -->|YAML File| ParseYAML[Parse YAML]
    LoadData -->|Dictionary| ValidateDict[Validate Dictionary]
    LoadData -->|Direct Creation| CreateEntity[Create Entity Instance]
    
    ParseYAML --> DateParser[Parse Date Fields]
    ValidateDict --> DateParser
    CreateEntity --> DateParser
    
    DateParser --> TypeValidation[Entity Type Validation]
    
    TypeValidation --> EntityTypeCheck{Entity Type Exists?}
    EntityTypeCheck -->|No| FallbackEntity[Create BaseEntity]
    EntityTypeCheck -->|Yes| SpecificEntity[Create Typed Entity]
    
    FallbackEntity --> CommonValidation[Common Field Validation]
    SpecificEntity --> FieldValidation[Field-Specific Validation]
    
    FieldValidation --> RequiredFields{All Required Fields Present?}
    RequiredFields -->|No| ValidationError[❌ Validation Error]
    RequiredFields -->|Yes| TypeChecking[Type Checking]
    
    TypeChecking --> RangeValidation[Range Validation]
    RangeValidation --> EnumValidation[Enum Validation]
    EnumValidation --> CrossFieldValidation[Cross-Field Validation]
    
    CrossFieldValidation --> DateValidation[Date Consistency]
    DateValidation --> CustomValidation[Custom Entity Validation]
    
    CommonValidation --> DateConsistency{End Date After Start Date?}
    DateConsistency -->|No| ValidationError
    DateConsistency -->|Yes| ExtraFields[Allow Extra Fields]
    
    CustomValidation --> EntitySpecificChecks{Entity-Specific Rules}
  
    %% Entity-specific validation branches
    EntitySpecificChecks -->|Employee| EmployeeValidation[Employee Validation]
    EntitySpecificChecks -->|Grant| GrantValidation[Grant Validation]
    EntitySpecificChecks -->|Investment| InvestmentValidation[Investment Validation]
    EntitySpecificChecks -->|Equipment| EquipmentValidation[Equipment Validation]
    EntitySpecificChecks -->|Project| ProjectValidation[Project Validation]
    EntitySpecificChecks -->|Other| StandardValidation[Standard Validation]
  
    %% Employee validation
    EmployeeValidation --> SalaryCheck{Salary > 0?}
    SalaryCheck -->|No| ValidationError
    SalaryCheck -->|Yes| OverheadCheck{Overhead 1.0-3.0?}
    OverheadCheck -->|No| ValidationError
    OverheadCheck -->|Yes| BonusCheck{Bonus 0-1.0?}
    BonusCheck -->|No| ValidationError
    BonusCheck -->|Yes| Success
  
    %% Grant validation
    GrantValidation --> AmountCheck{Amount > 0?}
    AmountCheck -->|No| ValidationError
    AmountCheck -->|Yes| IndirectRateCheck{Indirect Rate 0-1.0?}
    IndirectRateCheck -->|No| ValidationError
    IndirectRateCheck -->|Yes| MilestoneCheck{Milestone Amounts Valid?}
    MilestoneCheck -->|No| ValidationError
    MilestoneCheck -->|Yes| Success
  
    %% Investment validation
    InvestmentValidation --> InvestmentAmountCheck{Amount > 0?}
    InvestmentAmountCheck -->|No| ValidationError
    InvestmentAmountCheck -->|Yes| ValuationCheck{Valuation Consistent?}
    ValuationCheck -->|No| ValidationError
    ValuationCheck -->|Yes| Success
  
    %% Equipment validation
    EquipmentValidation --> CostCheck{Cost > 0?}
    CostCheck -->|No| ValidationError
    CostCheck -->|Yes| DepreciationCheck{Depreciation Method Valid?}
    DepreciationCheck -->|No| ValidationError
    DepreciationCheck -->|Yes| MaintenanceCheck{Maintenance % 0-1.0?}
    MaintenanceCheck -->|No| ValidationError
    MaintenanceCheck -->|Yes| Success
  
    %% Project validation
    ProjectValidation --> BudgetCheck{Budget > 0?}
    BudgetCheck -->|No| ValidationError
    BudgetCheck -->|Yes| CompletionCheck{Completion 0-100%?}
    CompletionCheck -->|No| ValidationError
    CompletionCheck -->|Yes| StatusCheck{Status Valid?}
    StatusCheck -->|No| ValidationError
    StatusCheck -->|Yes| Success
  
    StandardValidation --> Success
    ExtraFields --> Success
    
    Success([✅ Valid Entity Created])
    ValidationError --> ErrorDetails[Log Error Details]
    ErrorDetails --> End([❌ Creation Failed])

    %% Styling with accessible colors for black text
    classDef startEnd fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#000
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef decision fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000
    classDef validation fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    classDef error fill:#ffebee,stroke:#d32f2f,stroke-width:2px,color:#000
    classDef success fill:#e8f5e8,stroke:#4caf50,stroke-width:2px,color:#000

    class Start,End startEnd
    class ParseYAML,ValidateDict,CreateEntity,DateParser process
    class LoadData,EntityTypeCheck,RequiredFields,DateConsistency,EntitySpecificChecks decision
    class FieldValidation,TypeChecking,RangeValidation,CustomValidation validation
    class ValidationError,ErrorDetails error
    class Success success
```

## Validation Stages

### 1. Data Source Processing
- **YAML Parsing**: Convert YAML files to Python dictionaries
- **Date Parsing**: Transform ISO date strings to date objects
- **Type Inference**: Determine entity type from data

### 2. Entity Type Validation
- **Type Mapping**: Map entity type to appropriate class
- **Fallback Handling**: Use BaseEntity for unknown types
- **Configuration Check**: Verify type is configured in settings

### 3. Field Validation
- **Required Fields**: Ensure all mandatory fields are present
- **Type Checking**: Verify field types match expectations
- **Range Validation**: Check numeric values are within valid ranges
- **Enum Validation**: Validate enumerated values (status, frequency, etc.)

### 4. Cross-Field Validation
- **Date Consistency**: Ensure end_date > start_date
- **Logical Relationships**: Validate interdependent fields
- **Business Rules**: Apply domain-specific validation logic

### 5. Entity-Specific Validation

#### Employee Validation
- Salary must be positive
- Overhead multiplier between 1.0 and 3.0
- Bonus percentages between 0 and 1.0
- Pay frequency from valid options

#### Grant Validation
- Amount must be positive
- Indirect cost rate between 0 and 1.0
- Milestone amounts cannot exceed total grant amount

#### Investment Validation
- Amount must be positive
- Valuation data consistency
- Disbursement schedule validation

#### Equipment Validation
- Cost must be positive
- Depreciation method from valid options
- Maintenance percentage between 0 and 1.0

#### Project Validation
- Budget must be positive
- Completion percentage between 0 and 100
- Status from valid options
- Milestone date consistency

## Error Handling

### Validation Errors
When validation fails, the system provides detailed error messages:

```python
ValidationError: 1 validation error for Employee
salary
  Input should be greater than 0 [type=greater_than, input=-50000]
```

### Error Recovery
- **Partial Validation**: Continue processing other entities if one fails
- **Error Logging**: Record validation failures for review
- **Graceful Degradation**: Use BaseEntity for unparseable types

## Best Practices

### Data Quality
1. **Use ISO Date Formats**: Always use YYYY-MM-DD for dates
2. **Validate Early**: Check data before entity creation
3. **Handle Missing Data**: Provide sensible defaults where possible
4. **Document Constraints**: Clearly specify validation rules

### Performance
1. **Batch Validation**: Process multiple entities together
2. **Cache Validators**: Reuse validation logic across entities
3. **Lazy Loading**: Validate only when needed
4. **Early Exit**: Stop validation on first critical error