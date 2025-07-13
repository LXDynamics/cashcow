# Entity Relationships

```mermaid
erDiagram
    %% Core Business Entities
    EMPLOYEE {
        string id PK
        string name
        string role
        decimal base_salary
        decimal equity_percentage
        date start_date
        date end_date
        string entity_type
    }
    
    GRANT {
        string id PK
        string name
        decimal amount
        date award_date
        date start_date
        date end_date
        string entity_type
    }
    
    INVESTMENT {
        string id PK
        string name
        string investor
        decimal amount
        date investment_date
        string entity_type
    }
    
    SALE {
        string id PK
        string customer
        decimal amount
        date sale_date
        string product
        string entity_type
    }
    
    SERVICE {
        string id PK
        string name
        string client
        decimal contract_value
        date start_date
        date end_date
        string entity_type
    }
    
    FACILITY {
        string id PK
        string name
        string location
        decimal monthly_cost
        decimal square_footage
        string entity_type
    }
    
    SOFTWARE {
        string id PK
        string name
        string vendor
        decimal monthly_cost
        int license_count
        string entity_type
    }
    
    EQUIPMENT {
        string id PK
        string name
        decimal purchase_cost
        date purchase_date
        string assigned_to
        string location
        string entity_type
    }
    
    PROJECT {
        string id PK
        string name
        string description
        date start_date
        date end_date
        list team_members
        string entity_type
    }

    %% Relationships
    PROJECT ||--o{ EMPLOYEE : "has team members"
    EQUIPMENT ||--o| EMPLOYEE : "assigned to"
    EQUIPMENT ||--o| FACILITY : "located at"
    GRANT ||--o{ PROJECT : "funds milestones"
    SERVICE ||--o{ EMPLOYEE : "utilizes resources"
    EMPLOYEE ||--o| FACILITY : "works at"
    SOFTWARE ||--o{ EMPLOYEE : "licensed to"

    %% Styling for black text with accessible light backgrounds
    %%{init: {"theme": "base", "themeVariables": {
        "primaryColor": "#f8f9fa",
        "primaryTextColor": "#000000",
        "primaryBorderColor": "#6c757d",
        "lineColor": "#495057",
        "sectionBkgColor": "#e8f5e8",
        "altSectionBkgColor": "#fff3e0",
        "gridColor": "#dee2e6",
        "c0": "#e8f5e8",
        "c1": "#e1f5fe",
        "c2": "#fff3e0",
        "c3": "#f3e5f5",
        "c4": "#fce4ec",
        "c5": "#f1f8e9",
        "c6": "#fff8e1",
        "c7": "#e0f2f1"
    }}}%%
```

## Relationship Types

### Direct References
- **Project** → **Employee**: Projects can list team members by name
- **Equipment** → **Employee**: Equipment can be assigned to specific employees
- **Equipment** → **Facility**: Equipment can be located at specific facilities
- **Grant** → **Project**: Grant milestones can reference project deliverables

### Indirect Relationships
- **Service** → **Employee**: Service contracts may specify required employee hours
- **Software** → **Employee**: Software licenses are often allocated per employee
- **Facility** → **Employee**: Facilities house employees and determine overhead costs

### Configuration Dependencies
All entity types are configured through the `settings.yaml` file, which defines:
- Required fields for each entity type
- Default values and multipliers
- Validation rules and constraints
- Calculator assignments

### Storage Organization
```
entities/
├── revenue/
│   ├── grants/          # Grant YAML files
│   ├── investments/     # Investment YAML files  
│   ├── sales/          # Sale YAML files
│   └── services/       # Service YAML files
├── expenses/
│   ├── employees/      # Employee YAML files
│   ├── facilities/     # Facility YAML files
│   ├── softwares/      # Software YAML files
│   └── equipments/     # Equipment YAML files
└── projects/           # Project YAML files
```

## Data Flow

1. **Entity Creation**: Entities are created from YAML files or programmatically
2. **Validation**: Pydantic validators ensure data integrity
3. **Storage**: Entities are persisted as YAML files and aggregated in SQLite
4. **Calculation**: Entity methods calculate costs, revenues, and metrics
5. **Reporting**: Aggregated data feeds into reports and forecasts