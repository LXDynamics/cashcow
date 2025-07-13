---
title: Reports & Analysis Guide
sidebar_label: Reports & Analysis
sidebar_position: 4
description: Complete guide to CashCow's reporting capabilities and analysis tools
---

# CashCow Reports & Analysis Guide

This comprehensive guide covers all reporting capabilities, analysis tools, and output formats available in the CashCow financial forecasting system.

## Table of Contents

1. [Report Generation System](#report-generation-system)
2. [Available Report Types](#available-report-types)
3. [Output Formats](#output-formats)
4. [Analysis Tools](#analysis-tools)
5. [Visualization Capabilities](#visualization-capabilities)
6. [Report Customization](#report-customization)
7. [Automation & Scheduling](#automation--scheduling)
8. [CLI Usage](#cli-usage)
9. [Examples](#examples)

## Report Generation System

CashCow's reporting system is built around the `ReportGenerator` class, which provides a comprehensive suite of report generation capabilities with support for multiple output formats and customizable visualizations.

### Core Components

- **ReportGenerator**: Main report generation engine
- **Charts**: Matplotlib-based visualization system
- **Export Functions**: Multi-format export capabilities (HTML, CSV, Excel, PDF)
- **Template System**: Customizable report templates
- **Validation**: Data quality checks and error handling

### Architecture

```python
from cashcow.reports.generator import ReportGenerator
from cashcow.storage import EntityStore
from cashcow.engine import CashFlowEngine
from cashcow.engine.kpis import KPICalculator

# Initialize components
store = EntityStore("cashcow.db")
engine = CashFlowEngine(store)
kpi_calculator = KPICalculator()

# Create report generator
report_gen = ReportGenerator(
    output_dir="reports",
    store=store,
    engine=engine,
    kpi_calculator=kpi_calculator
)
```

## Available Report Types

### 1. Cash Flow Reports

**Primary cash flow visualization and analysis reports.**

#### Cash Flow Forecast Chart
- Line charts showing revenue, expenses, and net cash flow over time
- Cumulative cash balance with zero-line indicators
- Support for custom styling and color schemes

```python
chart_path = report_gen.generate_cash_flow_chart(
    df=cash_flow_data,
    title="Q1 2024 Cash Flow Forecast",
    style="seaborn-v0_8",
    figure_size=(16, 10),
    dpi=300
)
```

#### Revenue Breakdown
- Stacked area charts by revenue category
- Pie charts for revenue distribution
- Time-series analysis of revenue streams

#### Expense Analysis
- Quarterly expense breakdown by category
- Trend analysis for major expense categories
- Burn rate visualization and analysis

### 2. KPI Dashboard Reports

**Key Performance Indicator monitoring and analysis.**

#### Financial Health Dashboard
- Runway gauge charts with threshold indicators
- Burn rate vs. revenue comparison
- Growth metrics visualization
- Financial health scoring (0-100 scale)

```python
dashboard_path = report_gen.generate_kpi_dashboard(
    kpis=calculated_kpis,
    title="Financial Health Dashboard",
    filename="kpi_dashboard.png"
)
```

#### Runway Analysis
- Cash runway projections with warning zones
- Industry benchmark comparisons
- Risk assessment visualization

#### Burn Rate Analysis
- Monthly burn rate trends with regression lines
- Burn rate component breakdown
- Rolling averages and volatility analysis

### 3. Scenario Comparison Reports

**Multi-scenario analysis and comparison tools.**

#### Scenario Comparison Charts
- Side-by-side cash balance projections
- Revenue and expense comparisons across scenarios
- Summary metrics comparison tables

```python
comparison_path = report_gen.generate_scenario_comparison_chart(
    scenario_results={
        "baseline": baseline_df,
        "optimistic": optimistic_df,
        "conservative": conservative_df
    }
)
```

### 4. Executive Summary Reports

**High-level overview reports for stakeholders.**

#### Automated Executive Summary
- Key financial metrics overview
- Period-over-period analysis
- Highlights and concern identification
- Actionable recommendations

```python
exec_summary = report_gen.generate_executive_summary(
    df=cash_flow_data,
    kpis=calculated_kpis
)
```

### 5. Entity Breakdown Reports

**Detailed analysis of entity contributions.**

#### Entity Analysis by Type
- Entity counts and distribution
- Cost/revenue impact analysis
- Tag-based grouping and analysis

### 6. Risk Assessment Reports

**Comprehensive risk analysis and scoring.**

#### Risk Metrics
- Probability calculations (loss, runway depletion)
- Value-at-Risk (VaR) analysis
- Expected shortfall calculations
- Risk scoring with mitigation recommendations

## Output Formats

### 1. HTML Reports

**Rich, interactive web-based reports with embedded charts.**

Features:
- Responsive design with multiple themes (light, dark, blue)
- Embedded charts and visualizations
- Interactive KPI cards
- Data tables with formatting
- Custom CSS support

```python
html_path = report_gen.generate_html_report(
    df=cash_flow_data,
    kpis=calculated_kpis,
    scenario="baseline",
    theme="dark",
    include_charts=True,
    custom_css="body { font-family: 'Roboto', sans-serif; }"
)
```

### 2. CSV Exports

**Clean, structured data exports for analysis.**

```python
csv_path = report_gen.export_to_csv(
    df=cash_flow_data,
    filename="monthly_forecast"
)
```

### 3. Excel Reports

**Professional spreadsheets with formatting and multiple sheets.**

Features:
- Multiple worksheets (Forecast Data, KPIs)
- Professional formatting with headers and styling
- Auto-adjusted column widths
- Color-coded cells and conditional formatting

```python
excel_path = report_gen.export_to_excel(
    df=cash_flow_data,
    kpis=calculated_kpis,
    filename="financial_report"
)
```

### 4. PDF Reports

**Print-ready documents with professional formatting.**

```python
pdf_path = report_gen.generate_pdf_report(
    df=cash_flow_data,
    kpis=calculated_kpis,
    title="Q1 2024 Financial Report"
)
```

### 5. Complete Report Packages

**All-in-one packages with multiple formats and charts.**

```python
package_dir = report_gen.generate_complete_report_package(
    df=cash_flow_data,
    kpis=calculated_kpis,
    title="Comprehensive Financial Analysis",
    package_name="q1_2024_package"
)
```

Package contents:
- HTML report with embedded charts
- Excel workbook with multiple sheets
- CSV data export
- Individual chart files (PNG)
- KPIs JSON file
- All visualizations in high resolution

## Analysis Tools

### 1. Monte Carlo Simulation

**Probabilistic analysis with uncertainty modeling.**

#### Features
- Multi-parameter uncertainty modeling
- Correlation support between variables
- Parallel execution for performance
- Risk metric calculations
- Time-series percentile analysis

#### Distribution Support
- Normal distributions
- Uniform distributions
- Triangular distributions
- Log-normal distributions
- Beta distributions

```python
from cashcow.analysis.monte_carlo import MonteCarloSimulator, Distribution

# Create simulator
simulator = MonteCarloSimulator(engine, store)

# Add uncertainty models
simulator.add_uncertainty(
    entity_name="*",
    entity_type="employee",
    field="salary",
    distribution=Distribution("normal", {"mean": 1.0, "std": 0.1})
)

# Run simulation
results = simulator.run_simulation(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    num_simulations=1000,
    parallel=True
)
```

#### Simulation Results
- Percentile analysis (5%, 25%, 50%, 75%, 95%)
- Risk metrics (probability of loss, runway depletion)
- Value-at-Risk calculations
- Expected shortfall analysis
- Time-series confidence bands

### 2. What-If Analysis

**Scenario planning and sensitivity analysis tools.**

#### Features
- Single parameter sensitivity analysis
- Multi-parameter combination testing
- Breakeven analysis
- Scenario comparison
- Parameter optimization

```python
from cashcow.analysis.whatif import WhatIfAnalyzer, Parameter, WhatIfScenario

# Create analyzer
analyzer = WhatIfAnalyzer(engine, store)

# Create scenario
scenario = analyzer.create_scenario(
    name="growth_scenario",
    description="Aggressive growth with increased hiring"
)

# Add parameters
parameter = Parameter(
    name="engineer_salary",
    entity_name="Senior Engineer",
    entity_type="employee",
    field="salary",
    base_value=120000
)

# Run sensitivity analysis
sensitivity_results = analyzer.run_sensitivity_analysis(
    parameter=parameter,
    value_range=[100000, 110000, 120000, 130000, 140000],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)
```

#### Analysis Types

**Sensitivity Analysis**: Test how changes in a single parameter affect outcomes
**Multi-Parameter Analysis**: Test combinations of parameter changes
**Breakeven Analysis**: Find parameter values that achieve specific targets
**Scenario Comparison**: Compare multiple defined scenarios

## Visualization Capabilities

### Chart Types

1. **Line Charts**: Time-series data, trends, projections
2. **Area Charts**: Stacked revenue/expense categories
3. **Bar Charts**: Comparative analysis, quarterly summaries
4. **Pie Charts**: Proportional breakdowns
5. **Gauge Charts**: KPI indicators with thresholds
6. **Scatter Plots**: Correlation analysis
7. **Box Plots**: Distribution analysis from Monte Carlo

### Customization Options

#### Styling
- Multiple built-in themes (seaborn, classic, modern)
- Custom color schemes
- Figure size and DPI control
- Professional formatting

#### Chart Elements
- Custom titles and labels
- Legends and annotations
- Grid lines and reference lines
- Threshold indicators
- Trend lines and regression

```python
# Advanced chart customization
chart_path = report_gen.generate_cash_flow_chart(
    df=data,
    title="Custom Styled Forecast",
    style="seaborn-v0_8",
    color_scheme="viridis",
    figure_size=(20, 12),
    dpi=600
)
```

## Report Customization

### Custom Report Templates

Create specialized reports using the template system:

```python
template_config = {
    "title": "Board Report Q1 2024",
    "sections": [
        {
            "type": "summary",
            "title": "Executive Summary",
            "include_kpis": True
        },
        {
            "type": "chart",
            "title": "Financial Performance",
            "chart_type": "line",
            "data_source": "forecast"
        },
        {
            "type": "table",
            "title": "Monthly Breakdown",
            "data_source": "forecast",
            "columns": ["period", "total_revenue", "total_expenses", "cash_balance"]
        },
        {
            "type": "text",
            "title": "Risk Assessment",
            "content": "Current financial position shows strong growth potential..."
        }
    ]
}

custom_report = report_gen.generate_custom_report(
    df=cash_flow_data,
    kpis=calculated_kpis,
    template_config=template_config,
    filename="board_report_q1.html"
)
```

### Themes and Styling

#### Built-in Themes
- **Light Theme**: Clean, professional white background
- **Dark Theme**: Modern dark background with high contrast
- **Blue Theme**: Corporate blue color scheme

#### Custom CSS
```python
custom_css = """
.kpi-card { 
    border: 2px solid #3498db; 
    box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
}
.header { 
    background: linear-gradient(45deg, #3498db, #2980b9); 
}
"""

html_report = report_gen.generate_html_report(
    df=data,
    kpis=kpis,
    theme="custom",
    custom_css=custom_css
)
```

## Automation & Scheduling

### Automated Report Generation

```python
automation_config = {
    "frequency": "monthly",
    "reports": ["html_report", "kpi_dashboard", "cash_flow_chart"],
    "output_format": "timestamped",
    "archive_old_reports": True
}

automated_result = report_gen.generate_automated_report(
    df=cash_flow_data,
    kpis=calculated_kpis,
    automation_config=automation_config,
    run_timestamp=datetime.now()
)
```

### Scheduled Reporting Features
- Timestamped output directories
- Report archiving and cleanup
- Batch report generation
- Error handling and recovery
- Progress tracking and logging

## CLI Usage

### Generate Forecasts with Reports

```bash
# Generate basic forecast
poetry run cashcow forecast --months 12

# Generate forecast with scenario
poetry run cashcow forecast --months 24 --scenario optimistic

# Generate reports with custom output
poetry run cashcow forecast --months 12 --output-dir custom_reports
```

### Export Data

```bash
# Export to CSV
poetry run cashcow export --format csv --output forecast_data.csv

# Export to Excel
poetry run cashcow export --format excel --output financial_report.xlsx
```

## Examples

### Example 1: Basic Report Generation

```python
from datetime import date
from cashcow.storage import EntityStore
from cashcow.engine import CashFlowEngine
from cashcow.engine.kpis import KPICalculator
from cashcow.reports.generator import ReportGenerator

# Initialize system
store = EntityStore("example.db")
engine = CashFlowEngine(store)
kpi_calc = KPICalculator()
report_gen = ReportGenerator("reports", store, engine, kpi_calc)

# Generate forecast
df = engine.calculate_parallel(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# Calculate KPIs
kpis = kpi_calc.calculate_all_kpis(df)

# Generate comprehensive report
html_report = report_gen.generate_html_report(
    df=df,
    kpis=kpis,
    scenario="baseline",
    title="2024 Financial Forecast"
)

print(f"Report generated: {html_report}")
```

### Example 2: Monte Carlo Analysis with Reports

```python
from cashcow.analysis.monte_carlo import MonteCarloSimulator, Distribution

# Set up Monte Carlo simulation
simulator = MonteCarloSimulator(engine, store)

# Add uncertainties
simulator.add_uncertainty(
    entity_name="*",
    entity_type="employee",
    field="salary",
    distribution=Distribution("normal", {"mean": 1.0, "std": 0.15})
)

simulator.add_uncertainty(
    entity_name="*",
    entity_type="grant",
    field="amount",
    distribution=Distribution("triangular", {"left": 0.8, "mode": 1.0, "right": 1.3})
)

# Run simulation
mc_results = simulator.run_simulation(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    num_simulations=1000
)

# Generate Monte Carlo report with results
# (Custom reporting for MC results would be implemented)
print(f"Simulation complete: {mc_results['num_simulations']} runs")
print(f"Mean final balance: ${mc_results['summary']['mean_final_balance']:,.2f}")
print(f"Probability of positive balance: {mc_results['summary']['probability_positive_balance']:.2%}")
```

### Example 3: What-If Scenario Analysis

```python
from cashcow.analysis.whatif import WhatIfAnalyzer, Parameter

# Create analyzer
analyzer = WhatIfAnalyzer(engine, store)

# Create growth scenario
growth_scenario = analyzer.create_scenario(
    name="aggressive_growth",
    description="Aggressive hiring and expansion scenario"
)

# Add parameters
growth_scenario.add_parameter(Parameter(
    name="engineering_team_size",
    entity_name="*",
    entity_type="employee",
    field="salary",
    base_value=120000
))

# Run analysis
scenario_result = analyzer.calculate_scenario(
    growth_scenario,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# Generate scenario comparison report
comparison_results = analyzer.compare_scenarios(
    ["baseline", "aggressive_growth"],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# Generate comparison charts
comparison_chart = report_gen.generate_scenario_comparison_chart({
    "Baseline": baseline_df,
    "Growth": scenario_result['cash_flow']
})
```

### Example 4: Complete Report Package

```python
# Generate comprehensive report package
package = report_gen.generate_complete_report_package(
    df=df,
    kpis=kpis,
    title="Q1 2024 Board Report",
    package_name="q1_board_package"
)

print(f"Complete report package created at: {package}")
print("Package includes:")
print("- HTML report with charts")
print("- Excel workbook")
print("- CSV data export")
print("- Individual chart files")
print("- KPIs JSON data")
```

## Data Validation and Quality

The reporting system includes comprehensive data validation:

```python
# Validate data before reporting
validation_results = report_gen.validate_report_data(df, kpis)

if validation_results['is_valid']:
    print(f"Data quality score: {validation_results['data_quality_score']}/100")
else:
    print("Data validation errors:")
    for error in validation_results['errors']:
        print(f"  - {error}")
    
    print("Data validation warnings:")
    for warning in validation_results['warnings']:
        print(f"  - {warning}")
```

## Performance Considerations

### Large Dataset Handling
- Chunked processing for large datasets
- Memory-efficient data structures
- Parallel processing capabilities
- Progress reporting for long operations

### Chart Generation Optimization
- DPI optimization for file size vs. quality
- Selective chart generation
- Chart caching for repeated operations
- Memory cleanup for matplotlib figures

### Export Performance
- Streaming Excel exports for large datasets
- Compressed output options
- Incremental CSV writing
- Parallel export processing

## Troubleshooting

### Common Issues

1. **Memory Issues with Large Datasets**
   - Use chunked processing
   - Reduce chart resolution (DPI)
   - Enable garbage collection

2. **Chart Generation Errors**
   - Ensure matplotlib backend is properly configured
   - Check data types and NaN values
   - Verify sufficient disk space

3. **Export Format Issues**
   - Check openpyxl installation for Excel exports
   - Verify file permissions for output directory
   - Handle special characters in filenames

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Report generation with detailed logging
report_gen.generate_html_report(df, kpis, debug=True)
```

---

For additional examples and advanced usage patterns, see the `/docs/examples/` directory.
For technical implementation details, refer to the source code in `/src/cashcow/reports/` and `/src/cashcow/analysis/`.