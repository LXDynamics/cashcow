# Report Generation Pipeline

```mermaid
flowchart TD
    A[Entity Data] --> B[Cash Flow Engine]
    B --> C[Calculate Forecast]
    C --> D[Generate KPIs]
    D --> E[Report Generator]
    
    E --> F{Report Type}
    
    F -->|Charts| G[Chart Generation]
    F -->|HTML| H[HTML Report]
    F -->|Excel| I[Excel Export]
    F -->|CSV| J[CSV Export]
    F -->|PDF| K[PDF Generation]
    F -->|Package| L[Complete Package]
    
    G --> G1[Cash Flow Chart]
    G --> G2[Revenue Breakdown]
    G --> G3[Expense Analysis]
    G --> G4[KPI Dashboard]
    G --> G5[Scenario Comparison]
    G --> G6[Runway Analysis]
    
    H --> H1[Template Processing]
    H1 --> H2[Theme Application]
    H2 --> H3[Chart Embedding]
    H3 --> H4[HTML Output]
    
    I --> I1[Data Formatting]
    I1 --> I2[Multiple Sheets]
    I2 --> I3[Professional Styling]
    I3 --> I4[Excel Output]
    
    J --> J1[Data Cleaning]
    J1 --> J2[CSV Output]
    
    K --> K1[HTML Generation]
    K1 --> K2[PDF Conversion]
    K2 --> K3[PDF Output]
    
    L --> L1[Generate All Formats]
    L1 --> L2[Copy to Package Dir]
    L2 --> L3[Create Manifest]
    L3 --> L4[Package Output]
    
    M[Data Validation] --> E
    N[Error Handling] --> E
    O[Progress Tracking] --> E
    
    style A fill:#e1f5fe,color:#050505
    style E fill:#f3e5f5,color:#050505
    style F fill:#fff3e0,color:#050505
    style G fill:#e8f5e8,color:#050505
    style H fill:#fff8e1,color:#050505
    style I fill:#f3e5f5,color:#050505
    style J fill:#e1f5fe,color:#050505
    style K fill:#fce4ec,color:#050505
    style L fill:#f0f8ff,color:#050505
    
```

## Pipeline Stages

### 1. Data Input Stage
- **Entity Data**: Source entities from storage system
- **Cash Flow Engine**: Core calculation engine
- **Forecast Calculation**: Generate time-series financial data
- **KPI Generation**: Calculate key performance indicators

### 2. Validation Stage
- **Data Validation**: Check for data quality issues
- **Error Handling**: Manage calculation errors
- **Progress Tracking**: Monitor generation progress

### 3. Report Generation Stage
- **Report Type Selection**: Choose output format
- **Template Processing**: Apply report templates
- **Data Formatting**: Format data for output

### 4. Chart Generation
- **Cash Flow Charts**: Primary financial visualizations
- **Breakdown Charts**: Revenue and expense analysis
- **KPI Dashboards**: Performance indicator displays
- **Comparative Charts**: Scenario and trend analysis

### 5. Output Generation
- **HTML Reports**: Rich web-based reports
- **Excel Exports**: Professional spreadsheets
- **CSV Exports**: Raw data exports
- **PDF Reports**: Print-ready documents
- **Complete Packages**: All formats combined

### 6. Post-Processing
- **File Organization**: Structure output files
- **Metadata Generation**: Create report manifests
- **Archive Management**: Handle report versioning