# Analysis Tool Workflows

```mermaid
flowchart TD
    A[Entity Store] --> B{Analysis Type}
    
    B -->|Monte Carlo| C[Monte Carlo Simulator]
    B -->|What-If| D[What-If Analyzer]
    B -->|Sensitivity| E[Sensitivity Analysis]
    B -->|Scenario| F[Scenario Comparison]
    
    %% Monte Carlo Workflow
    C --> C1[Define Uncertainties]
    C1 --> C2[Set Distributions]
    C2 --> C3[Configure Correlations]
    C3 --> C4[Generate Samples]
    C4 --> C5{Parallel Mode?}
    C5 -->|Yes| C6[Multi-threaded Execution]
    C5 -->|No| C7[Sequential Execution]
    C6 --> C8[Aggregate Results]
    C7 --> C8
    C8 --> C9[Statistical Analysis]
    C9 --> C10[Risk Metrics]
    C10 --> C11[Time Series Percentiles]
    C11 --> MC_OUT[Monte Carlo Results]
    
    %% What-If Workflow
    D --> D1[Create Scenarios]
    D1 --> D2[Define Parameters]
    D2 --> D3[Set Value Ranges]
    D3 --> D4[Apply Changes to Entities]
    D4 --> D5[Run Calculations]
    D5 --> D6[Compare Outcomes]
    D6 --> D7[Generate Insights]
    D7 --> WI_OUT[What-If Results]
    
    %% Sensitivity Analysis
    E --> E1[Select Parameter]
    E1 --> E2[Define Test Range]
    E2 --> E3[Single Parameter Variation]
    E3 --> E4[Calculate Impact]
    E4 --> E5[Correlation Analysis]
    E5 --> E6[Elasticity Calculation]
    E6 --> SENS_OUT[Sensitivity Results]
    
    %% Scenario Comparison
    F --> F1[Load Multiple Scenarios]
    F1 --> F2[Run Each Scenario]
    F2 --> F3[Extract Key Metrics]
    F3 --> F4[Statistical Comparison]
    F4 --> F5[Best/Worst Analysis]
    F5 --> SCEN_OUT[Comparison Results]
    
    %% Common Processing
    MC_OUT --> G[Result Processing]
    WI_OUT --> G
    SENS_OUT --> G
    SCEN_OUT --> G
    
    G --> H[Data Aggregation]
    H --> I[Visualization Preparation]
    I --> J[Report Integration]
    J --> K[Export to Formats]
    
    %% Output Types
    K --> K1[Charts & Graphs]
    K --> K2[Statistical Tables]
    K --> K3[Risk Assessment]
    K --> K4[Recommendations]
    
    style A fill:#e1f5fe,color:#000
    style B fill:#fff3e0,color:#000
    style C fill:#e8f5e8,color:#000
    style D fill:#f3e5f5,color:#000
    style E fill:#fff8e1,color:#000
    style F fill:#f1f8e9,color:#000
    style G fill:#fce4ec,color:#000
    style MC_OUT fill:#e8f5e8,color:#000
    style WI_OUT fill:#e8f5e8,color:#000
    style SENS_OUT fill:#e8f5e8,color:#000
    style SCEN_OUT fill:#e8f5e8,color:#000
    
 
```

## Analysis Workflow Details

### Monte Carlo Simulation Workflow

```mermaid
sequenceDiagram
    participant User
    participant Simulator
    participant Engine
    participant Store
    participant Workers
    
    User->>Simulator: Configure uncertainties
    User->>Simulator: Set distributions
    User->>Simulator: Run simulation
    
    Simulator->>Simulator: Generate sample sets
    Simulator->>Workers: Distribute work
    
    loop For each simulation
        Workers->>Store: Create temp entities
        Workers->>Engine: Calculate cash flow
        Workers->>Engine: Calculate KPIs
        Workers->>Simulator: Return results
    end
    
    Simulator->>Simulator: Aggregate results
    Simulator->>Simulator: Calculate statistics
    Simulator->>User: Return analysis
```

### What-If Analysis Workflow

```mermaid
sequenceDiagram
    participant User
    participant Analyzer
    participant Scenario
    participant Engine
    participant Store
    
    User->>Analyzer: Create scenario
    User->>Scenario: Add parameters
    User->>Scenario: Set value ranges
    
    loop For each parameter combination
        Analyzer->>Store: Apply parameter changes
        Analyzer->>Engine: Calculate forecast
        Analyzer->>Analyzer: Store results
    end
    
    Analyzer->>Analyzer: Compare scenarios
    Analyzer->>Analyzer: Calculate sensitivity
    Analyzer->>User: Return analysis
```

### Sensitivity Analysis Process

```mermaid
flowchart LR
    A[Parameter Selection] --> B[Value Range Definition]
    B --> C[Systematic Variation]
    C --> D[Impact Measurement]
    D --> E[Correlation Analysis]
    E --> F[Elasticity Calculation]
    F --> G[Sensitivity Ranking]
    G --> H[Visualization]
    H --> I[Insights Generation]
    
    style A fill:#fff8e1,color:#000
    style D fill:#e8f5e8,color:#000
    style G fill:#e1f5fe,color:#000
    style I fill:#f3e5f5,color:#000
    
 
```

## Analysis Types and Capabilities

### 1. Monte Carlo Simulation
- **Purpose**: Probabilistic risk analysis
- **Input**: Uncertainty distributions for key parameters
- **Output**: Statistical distributions of outcomes
- **Metrics**: VaR, Expected Shortfall, Confidence Intervals

### 2. What-If Analysis
- **Purpose**: Scenario planning and impact assessment
- **Input**: Parameter changes and scenarios
- **Output**: Comparative scenario outcomes
- **Metrics**: Sensitivity coefficients, breakeven points

### 3. Sensitivity Analysis
- **Purpose**: Parameter importance ranking
- **Input**: Single parameter variations
- **Output**: Impact correlation and elasticity
- **Metrics**: Correlation coefficients, elasticity measures

### 4. Scenario Comparison
- **Purpose**: Multi-scenario evaluation
- **Input**: Multiple defined scenarios
- **Output**: Comparative analysis and rankings
- **Metrics**: Best/worst case identification, variance analysis

## Analysis Result Processing

```mermaid
flowchart TD
    A[Raw Analysis Results] --> B[Data Cleaning]
    B --> C[Statistical Processing]
    C --> D[Metric Calculation]
    D --> E[Ranking & Comparison]
    E --> F[Insight Generation]
    F --> G[Visualization Prep]
    G --> H[Report Integration]
    
    H --> I[Charts]
    H --> J[Tables]
    H --> K[Summaries]
    H --> L[Recommendations]
    
    style A fill:#fff8e1,color:#000
    style F fill:#e8f5e8,color:#000
    style H fill:#e1f5fe,color:#000
    
 
```

## Performance Optimization

### Parallel Processing Strategy
1. **Work Distribution**: Split simulations across worker threads
2. **Memory Management**: Use temporary in-memory stores
3. **Result Aggregation**: Efficient statistical calculations
4. **Progress Tracking**: Real-time progress reporting

### Efficiency Considerations
- **Batch Processing**: Group similar calculations
- **Caching**: Reuse intermediate results
- **Memory Cleanup**: Garbage collection for large datasets
- **Error Recovery**: Robust error handling and continuation