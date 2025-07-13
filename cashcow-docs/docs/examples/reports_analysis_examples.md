# Reports & Analysis Examples

This document provides practical examples of using CashCow's reporting and analysis capabilities for various business scenarios.

## Table of Contents

1. [Basic Report Generation](#basic-report-generation)
2. [Custom Report Templates](#custom-report-templates)
3. [Monte Carlo Risk Analysis](#monte-carlo-risk-analysis)
4. [What-If Scenario Planning](#what-if-scenario-planning)
5. [Sensitivity Analysis](#sensitivity-analysis)
6. [Executive Dashboard](#executive-dashboard)
7. [Investor Reports](#investor-reports)
8. [Monthly Operations Reports](#monthly-operations-reports)

## Basic Report Generation

### Example 1: Quarterly Financial Report

```python
from datetime import date
from cashcow.storage import EntityStore
from cashcow.engine import CashFlowEngine
from cashcow.engine.kpis import KPICalculator
from cashcow.reports.generator import ReportGenerator

# Initialize the reporting system
store = EntityStore("company_data.db")
engine = CashFlowEngine(store)
kpi_calculator = KPICalculator()
report_gen = ReportGenerator("quarterly_reports", store, engine, kpi_calculator)

# Generate Q1 2024 forecast
start_date = date(2024, 1, 1)
end_date = date(2024, 3, 31)

# Calculate forecast and KPIs
forecast_df = engine.calculate_parallel(start_date, end_date)
kpis = kpi_calculator.calculate_all_kpis(forecast_df)

# Generate comprehensive HTML report
html_report = report_gen.generate_html_report(
    df=forecast_df,
    kpis=kpis,
    scenario="q1_baseline",
    title="Q1 2024 Financial Forecast",
    theme="professional",
    include_charts=True
)

# Export to multiple formats
excel_report = report_gen.export_to_excel(
    df=forecast_df,
    kpis=kpis,
    filename="q1_2024_forecast"
)

csv_export = report_gen.export_to_csv(
    df=forecast_df,
    filename="q1_2024_data"
)

print(f"Q1 2024 reports generated:")
print(f"  HTML: {html_report}")
print(f"  Excel: {excel_report}")
print(f"  CSV: {csv_export}")
```

### Example 2: KPI Dashboard for Management

```python
# Generate focused KPI dashboard
kpi_dashboard = report_gen.generate_kpi_dashboard(
    kpis=kpis,
    title="Management Dashboard - Q1 2024",
    filename="management_dashboard.png"
)

# Generate runway analysis
runway_chart = report_gen.generate_runway_analysis_chart(
    df=forecast_df,
    kpis=kpis
)

# Generate burn rate analysis
burn_chart = report_gen.generate_burn_rate_chart(df=forecast_df)

print(f"KPI Dashboard: {kpi_dashboard}")
print(f"Runway Analysis: {runway_chart}")
print(f"Burn Rate Chart: {burn_chart}")
```

## Custom Report Templates

### Example 3: Board of Directors Report

```python
# Custom template for board presentation
board_template = {
    "title": "Board Report - Q1 2024",
    "sections": [
        {
            "type": "summary",
            "title": "Executive Summary",
            "include_kpis": True
        },
        {
            "type": "chart",
            "title": "Financial Performance Overview",
            "chart_type": "line",
            "data_source": "forecast"
        },
        {
            "type": "text",
            "title": "Key Achievements",
            "content": """
            <h4>Q1 2024 Highlights:</h4>
            <ul>
                <li>Secured $1.5M Series A funding</li>
                <li>Hired 3 senior engineers</li>
                <li>Launched MVP with 100+ beta users</li>
                <li>Extended runway to 18 months</li>
            </ul>
            """
        },
        {
            "type": "chart",
            "title": "Runway Analysis",
            "chart_type": "runway",
            "data_source": "kpis"
        },
        {
            "type": "table",
            "title": "Monthly Financial Summary",
            "data_source": "forecast",
            "columns": ["period", "total_revenue", "total_expenses", "net_cash_flow", "cash_balance"]
        },
        {
            "type": "text",
            "title": "Risk Assessment & Mitigation",
            "content": """
            <h4>Key Risks:</h4>
            <ul>
                <li><strong>Market Risk:</strong> Competitive landscape evolving rapidly</li>
                <li><strong>Operational Risk:</strong> Key person dependency in engineering</li>
                <li><strong>Financial Risk:</strong> Revenue concentration in early customers</li>
            </ul>
            <h4>Mitigation Strategies:</h4>
            <ul>
                <li>Diversifying customer base through sales expansion</li>
                <li>Building redundancy in technical leadership</li>
                <li>Maintaining 12+ month cash runway at all times</li>
            </ul>
            """
        }
    ]
}

# Generate custom board report
board_report = report_gen.generate_custom_report(
    df=forecast_df,
    kpis=kpis,
    template_config=board_template,
    filename="board_report_q1_2024.html"
)

print(f"Board report generated: {board_report}")
```

### Example 4: Investor Update Template

```python
# Template for monthly investor updates
investor_template = {
    "title": "Investor Update - March 2024",
    "sections": [
        {
            "type": "summary",
            "title": "Key Metrics",
            "include_kpis": True
        },
        {
            "type": "text",
            "title": "Progress Update",
            "content": """
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h4>🚀 Product Development</h4>
                <p>Completed integration with major aerospace suppliers. Beta testing shows 25% improvement in efficiency.</p>
                
                <h4>📈 Business Growth</h4>
                <p>Signed 2 new enterprise customers. Monthly recurring revenue increased by 40%.</p>
                
                <h4>👥 Team Expansion</h4>
                <p>Hired VP of Sales and 2 senior engineers. Team now at 15 full-time employees.</p>
                
                <h4>💰 Financial Health</h4>
                <p>Runway extended to 18 months. Burn rate stable at $120K/month.</p>
            </div>
            """
        },
        {
            "type": "chart",
            "title": "Monthly Revenue Growth",
            "chart_type": "line",
            "data_source": "forecast"
        }
    ]
}

investor_update = report_gen.generate_custom_report(
    df=forecast_df,
    kpis=kpis,
    template_config=investor_template,
    filename="investor_update_march_2024.html"
)

print(f"Investor update generated: {investor_update}")
```

## Monte Carlo Risk Analysis

### Example 5: Fundraising Risk Assessment

```python
from cashcow.analysis.monte_carlo import MonteCarloSimulator, Distribution

# Initialize Monte Carlo simulator
mc_simulator = MonteCarloSimulator(engine, store)

# Model uncertainties in key parameters
# Revenue uncertainty (customer acquisition variability)
mc_simulator.add_uncertainty(
    entity_name="*",
    entity_type="sale",
    field="amount",
    distribution=Distribution("lognormal", {"mean": 0.0, "sigma": 0.4})
)

# Employee salary uncertainty (market competition)
mc_simulator.add_uncertainty(
    entity_name="*",
    entity_type="employee",
    field="salary",
    distribution=Distribution("normal", {"mean": 1.0, "std": 0.12})
)

# Grant funding uncertainty (approval delays)
mc_simulator.add_uncertainty(
    entity_name="SBIR*",
    entity_type="grant",
    field="amount",
    distribution=Distribution("triangular", {"left": 0.7, "mode": 1.0, "right": 1.0})
)

# Investment timing uncertainty
mc_simulator.add_uncertainty(
    entity_name="Series A",
    entity_type="investment",
    field="start_date",
    distribution=Distribution("uniform", {"low": -30, "high": 90})  # days variation
)

# Run simulation
print("Running Monte Carlo simulation for fundraising scenarios...")
mc_results = mc_simulator.run_simulation(
    start_date=date(2024, 1, 1),
    end_date=date(2025, 12, 31),
    num_simulations=2000,
    confidence_levels=[0.05, 0.25, 0.5, 0.75, 0.95],
    parallel=True,
    max_workers=6
)

# Analyze results
print(f"\n=== MONTE CARLO RISK ANALYSIS ===")
print(f"Simulations run: {mc_results['num_simulations']}")
print(f"Mean final cash balance: ${mc_results['summary']['mean_final_balance']:,.0f}")
print(f"Probability of positive balance: {mc_results['summary']['probability_positive_balance']:.1%}")
print(f"Probability of runway > 12 months: {mc_results['summary']['probability_runway_gt_12m']:.1%}")
print(f"Value at Risk (5%): ${mc_results['summary']['value_at_risk_5pct']:,.0f}")

# Risk assessment
risk_metrics = mc_results['risk_metrics']
print(f"\n=== RISK METRICS ===")
print(f"Probability of loss: {risk_metrics['probability_of_loss']:.1%}")
print(f"Probability of runway < 6 months: {risk_metrics['probability_runway_lt_6m']:.1%}")
print(f"Worst case 5% scenario: ${risk_metrics['worst_case_5pct']:,.0f}")
print(f"Best case 95% scenario: ${risk_metrics['best_case_95pct']:,.0f}")

# Save detailed results
from cashcow.analysis.monte_carlo import save_simulation_results
save_simulation_results(mc_results, "monte_carlo_fundraising_analysis.json")

print(f"\nDetailed results saved to: monte_carlo_fundraising_analysis.json")
```

### Example 6: Market Expansion Risk Analysis

```python
# Scenario: Expanding to European market
# Model the additional uncertainties

# European sales uncertainty (market entry risk)
mc_simulator.add_uncertainty(
    entity_name="EU_Sales*",
    entity_type="sale",
    field="amount",
    distribution=Distribution("beta", {"a": 2, "b": 5})  # Skewed toward lower values initially
)

# Additional European team costs
mc_simulator.add_uncertainty(
    entity_name="EU_*",
    entity_type="employee",
    field="salary",
    distribution=Distribution("normal", {"mean": 1.15, "std": 0.08})  # 15% higher salaries
)

# EU facility costs (regulatory and setup uncertainties)
mc_simulator.add_uncertainty(
    entity_name="EU_Office",
    entity_type="facility",
    field="monthly_cost",
    distribution=Distribution("triangular", {"left": 8000, "mode": 12000, "right": 18000})
)

# Run expansion analysis
expansion_results = mc_simulator.run_simulation(
    start_date=date(2024, 6, 1),  # Start expansion mid-year
    end_date=date(2025, 12, 31),
    num_simulations=1500,
    parallel=True
)

print(f"\n=== EU EXPANSION RISK ANALYSIS ===")
print(f"Expected impact on final balance: ${expansion_results['summary']['mean_final_balance']:,.0f}")
print(f"Success probability (positive ROI): {expansion_results['summary']['probability_positive_balance']:.1%}")

# Compare with baseline scenario
baseline_mean = mc_results['summary']['mean_final_balance']
expansion_mean = expansion_results['summary']['mean_final_balance']
expansion_value = expansion_mean - baseline_mean

print(f"Net value of expansion: ${expansion_value:,.0f}")
print(f"Expansion ROI probability > 20%: {(expansion_value / baseline_mean > 0.2)}")
```

## What-If Scenario Planning

### Example 7: Hiring Plan Optimization

```python
from cashcow.analysis.whatif import WhatIfAnalyzer, Parameter, WhatIfScenario

# Initialize What-If analyzer
whatif_analyzer = WhatIfAnalyzer(engine, store)

# Create hiring scenarios
conservative_scenario = whatif_analyzer.create_scenario(
    name="conservative_hiring",
    description="Minimal hiring to extend runway"
)

aggressive_scenario = whatif_analyzer.create_scenario(
    name="aggressive_hiring", 
    description="Rapid team expansion for growth"
)

balanced_scenario = whatif_analyzer.create_scenario(
    name="balanced_hiring",
    description="Moderate hiring balanced with runway"
)

# Add parameters for different roles
engineer_positions = Parameter(
    name="engineering_headcount",
    entity_name="Engineer*",
    entity_type="employee",
    field="salary",
    base_value=120000
)

sales_positions = Parameter(
    name="sales_headcount", 
    entity_name="Sales*",
    entity_type="employee",
    field="salary",
    base_value=90000
)

# Configure scenarios
# Conservative: Current team + 1 engineer
conservative_scenario.add_parameter(engineer_positions)
conservative_scenario.set_parameter_value("engineering_headcount", 120000)  # 1 person

# Aggressive: Add 3 engineers + 2 sales people
aggressive_scenario.add_parameter(engineer_positions)
aggressive_scenario.add_parameter(sales_positions)
aggressive_scenario.set_parameter_value("engineering_headcount", 360000)  # 3 people
aggressive_scenario.set_parameter_value("sales_headcount", 180000)  # 2 people

# Balanced: Add 2 engineers + 1 sales person
balanced_scenario.add_parameter(engineer_positions)
balanced_scenario.add_parameter(sales_positions)
balanced_scenario.set_parameter_value("engineering_headcount", 240000)  # 2 people
balanced_scenario.set_parameter_value("sales_headcount", 90000)  # 1 person

# Run scenario comparison
scenario_comparison = whatif_analyzer.compare_scenarios(
    ["conservative_hiring", "aggressive_hiring", "balanced_hiring"],
    start_date=date(2024, 4, 1),
    end_date=date(2025, 12, 31)
)

print(f"\n=== HIRING SCENARIO COMPARISON ===")
for scenario in scenario_comparison['comparison_table']:
    name = scenario['scenario_name']
    runway = scenario['runway_months']
    final_balance = scenario['final_cash_balance']
    print(f"{name:20s}: Runway {runway:5.1f} months, Final Balance ${final_balance:>10,.0f}")

# Find optimal hiring pace
print(f"\nBest scenarios by metric:")
for metric, scenario in scenario_comparison['best_scenarios'].items():
    print(f"  {metric:20s}: {scenario}")
```

### Example 8: Revenue Model Sensitivity

```python
# Test sensitivity to different revenue assumptions
revenue_parameter = Parameter(
    name="monthly_revenue_growth",
    entity_name="Monthly_Sales",
    entity_type="sale", 
    field="amount",
    base_value=50000
)

# Test different monthly revenue levels
revenue_range = [25000, 35000, 50000, 75000, 100000, 150000]

revenue_sensitivity = whatif_analyzer.run_sensitivity_analysis(
    parameter=revenue_parameter,
    value_range=revenue_range,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

print(f"\n=== REVENUE SENSITIVITY ANALYSIS ===")
print(f"Parameter: {revenue_parameter.name}")
print(f"Base value: ${revenue_parameter.base_value:,.0f}")

for i, revenue in enumerate(revenue_range):
    scenario = revenue_sensitivity['scenarios'][i]
    final_balance = revenue_sensitivity['metrics']['final_cash_balance'][i]
    runway = revenue_sensitivity['metrics']['runway_months'][i]
    
    print(f"Revenue ${revenue:>6,.0f}: Balance ${final_balance:>10,.0f}, Runway {runway:5.1f} months")

# Calculate revenue breakeven point
breakeven_analysis = whatif_analyzer.find_breakeven_value(
    parameter=revenue_parameter,
    target_metric="final_cash_balance",
    target_value=0,  # Break even
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    search_range=(20000, 200000)
)

if breakeven_analysis['converged']:
    breakeven_revenue = breakeven_analysis['breakeven_value']
    print(f"\nBreakeven monthly revenue: ${breakeven_revenue:,.0f}")
else:
    print(f"\nBreakeven analysis did not converge")
```

## Sensitivity Analysis

### Example 9: Multi-Parameter Sensitivity Study

```python
# Study sensitivity across multiple key parameters
multi_param_ranges = {
    "engineer_salary": [100000, 110000, 120000, 130000, 140000],
    "office_rent": [8000, 10000, 12000, 15000, 18000],
    "customer_acquisition": [30000, 40000, 50000, 65000, 80000],
    "grant_probability": [0.6, 0.7, 0.8, 0.9, 1.0]
}

# Create base scenario for multi-parameter analysis
multi_param_scenario = whatif_analyzer.create_scenario(
    name="sensitivity_base",
    description="Base scenario for multi-parameter sensitivity"
)

# Add all parameters
multi_param_scenario.add_parameter(Parameter(
    name="engineer_salary",
    entity_name="Engineer*",
    entity_type="employee", 
    field="salary",
    base_value=120000
))

multi_param_scenario.add_parameter(Parameter(
    name="office_rent",
    entity_name="Main_Office",
    entity_type="facility",
    field="monthly_cost", 
    base_value=12000
))

multi_param_scenario.add_parameter(Parameter(
    name="customer_acquisition",
    entity_name="Monthly_Sales",
    entity_type="sale",
    field="amount",
    base_value=50000
))

# Run multi-parameter analysis
multi_results = whatif_analyzer.run_multi_parameter_analysis(
    scenario=multi_param_scenario,
    parameter_ranges=multi_param_ranges,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    max_combinations=50  # Limit combinations for performance
)

print(f"\n=== MULTI-PARAMETER SENSITIVITY ===")
print(f"Tested {multi_results['num_combinations']} parameter combinations")

# Summary statistics
stats = multi_results['summary_stats']
print(f"\nFinal Cash Balance Statistics:")
print(f"  Mean: ${stats['metrics']['final_cash_balance']['mean']:,.0f}")
print(f"  Std:  ${stats['metrics']['final_cash_balance']['std']:,.0f}") 
print(f"  Min:  ${stats['metrics']['final_cash_balance']['min']:,.0f}")
print(f"  Max:  ${stats['metrics']['final_cash_balance']['max']:,.0f}")

# Best and worst combinations
best = stats['best_combination']
worst = stats['worst_combination']

print(f"\nBest Parameter Combination:")
for param, value in best['parameters'].items():
    print(f"  {param}: ${value:,.0f}" if 'salary' in param or 'rent' in param or 'acquisition' in param else f"  {param}: {value}")
print(f"  Result: ${best['final_cash_balance']:,.0f}")

print(f"\nWorst Parameter Combination:")
for param, value in worst['parameters'].items():
    print(f"  {param}: ${value:,.0f}" if 'salary' in param or 'rent' in param or 'acquisition' in param else f"  {param}: {value}")
print(f"  Result: ${worst['final_cash_balance']:,.0f}")

print(f"\nSuccess rate (positive balance): {stats['success_rate']:.1%}")
```

## Executive Dashboard

### Example 10: Real-Time Executive Dashboard

```python
# Create comprehensive executive dashboard
def generate_executive_dashboard():
    # Get latest data
    current_forecast = engine.calculate_parallel(
        start_date=date.today(),
        end_date=date(2024, 12, 31)
    )
    current_kpis = kpi_calculator.calculate_all_kpis(current_forecast)
    
    # Generate executive summary
    exec_summary = report_gen.generate_executive_summary(
        df=current_forecast,
        kpis=current_kpis
    )
    
    # Create dashboard template
    dashboard_template = {
        "title": f"Executive Dashboard - {date.today().strftime('%B %Y')}",
        "sections": [
            {
                "type": "summary",
                "title": "Financial Overview",
                "include_kpis": True
            },
            {
                "type": "text",
                "title": "Key Insights",
                "content": f"""
                <div class="insights-grid">
                    <div class="insight-card positive">
                        <h4>💰 Financial Position</h4>
                        <p>{exec_summary['highlights'][0] if exec_summary['highlights'] else 'Strong financial position maintained'}</p>
                    </div>
                    <div class="insight-card warning">
                        <h4>⚠️ Key Risks</h4>
                        <p>{exec_summary['concerns'][0] if exec_summary['concerns'] else 'No major concerns identified'}</p>
                    </div>
                    <div class="insight-card action">
                        <h4>🎯 Action Items</h4>
                        <p>{exec_summary['recommendations'][0] if exec_summary['recommendations'] else 'Continue current trajectory'}</p>
                    </div>
                </div>
                """
            }
        ]
    }
    
    # Generate dashboard
    dashboard_path = report_gen.generate_custom_report(
        df=current_forecast,
        kpis=current_kpis,
        template_config=dashboard_template,
        filename=f"executive_dashboard_{date.today().strftime('%Y_%m_%d')}.html"
    )
    
    # Generate supporting charts
    kpi_dashboard = report_gen.generate_kpi_dashboard(
        kpis=current_kpis,
        title="Executive KPI Dashboard"
    )
    
    runway_analysis = report_gen.generate_runway_analysis_chart(
        df=current_forecast,
        kpis=current_kpis
    )
    
    return {
        'dashboard': dashboard_path,
        'kpi_chart': kpi_dashboard,
        'runway_chart': runway_analysis,
        'summary': exec_summary
    }

# Generate dashboard
dashboard_results = generate_executive_dashboard()
print(f"Executive dashboard generated: {dashboard_results['dashboard']}")
print(f"Supporting charts: {dashboard_results['kpi_chart']}, {dashboard_results['runway_chart']}")
```

## Investor Reports

### Example 11: Series A Investor Deck Data

```python
# Generate data for investor presentation
def prepare_investor_data():
    # 24-month projection for investor presentation
    investor_forecast = engine.calculate_parallel(
        start_date=date(2024, 1, 1),
        end_date=date(2025, 12, 31)
    )
    investor_kpis = kpi_calculator.calculate_all_kpis(investor_forecast)
    
    # Run growth scenarios for investor presentation
    scenarios = {
        "conservative": {"revenue_multiplier": 0.8, "hiring_delay": 3},
        "baseline": {"revenue_multiplier": 1.0, "hiring_delay": 0}, 
        "optimistic": {"revenue_multiplier": 1.5, "hiring_delay": -1}
    }
    
    scenario_results = {}
    for scenario_name, params in scenarios.items():
        # This would involve creating modified entities based on parameters
        # For simplicity, we'll use the baseline forecast
        scenario_results[scenario_name] = investor_forecast
    
    # Generate scenario comparison
    scenario_chart = report_gen.generate_scenario_comparison_chart(scenario_results)
    
    # Create investor-focused metrics
    investor_metrics = {
        "current_runway_months": investor_kpis.get('runway_months', 0),
        "monthly_burn_rate": abs(investor_kpis.get('burn_rate', 0)),
        "projected_revenue_24m": investor_forecast['total_revenue'].sum(),
        "team_size_growth": 15,  # Current team to projected team
        "market_opportunity": 2.5e9,  # $2.5B TAM
        "customer_acquisition_cost": 5000,
        "lifetime_value": 50000,
        "gross_margin": 0.75
    }
    
    # Generate investor report
    investor_template = {
        "title": "Series A Investment Opportunity",
        "sections": [
            {
                "type": "text",
                "title": "Investment Highlights",
                "content": f"""
                <div class="investment-highlights">
                    <div class="highlight-row">
                        <div class="metric">
                            <h3>${investor_metrics['projected_revenue_24m']/1e6:.1f}M</h3>
                            <p>24-Month Revenue Projection</p>
                        </div>
                        <div class="metric">
                            <h3>{investor_metrics['current_runway_months']:.0f} months</h3>
                            <p>Current Runway</p>
                        </div>
                        <div class="metric">
                            <h3>{investor_metrics['team_size_growth']}x</h3>
                            <p>Team Growth Planned</p>
                        </div>
                    </div>
                    <div class="highlight-row">
                        <div class="metric">
                            <h3>${investor_metrics['market_opportunity']/1e9:.1f}B</h3>
                            <p>Total Addressable Market</p>
                        </div>
                        <div class="metric">
                            <h3>{investor_metrics['gross_margin']:.0%}</h3>
                            <p>Gross Margin</p>
                        </div>
                        <div class="metric">
                            <h3>{investor_metrics['lifetime_value']/investor_metrics['customer_acquisition_cost']:.1f}x</h3>
                            <p>LTV/CAC Ratio</p>
                        </div>
                    </div>
                </div>
                """
            },
            {
                "type": "chart",
                "title": "Growth Scenarios",
                "chart_type": "scenario_comparison",
                "data_source": "scenarios"
            }
        ]
    }
    
    investor_report = report_gen.generate_custom_report(
        df=investor_forecast,
        kpis=investor_kpis,
        template_config=investor_template,
        filename="series_a_investor_report.html"
    )
    
    return {
        'report': investor_report,
        'metrics': investor_metrics,
        'scenario_chart': scenario_chart
    }

investor_data = prepare_investor_data()
print(f"Investor report generated: {investor_data['report']}")
print(f"Key metrics prepared for presentation deck")
```

## Monthly Operations Reports

### Example 12: Automated Monthly Report

```python
from datetime import datetime

def generate_monthly_operations_report(month_year):
    """Generate automated monthly operations report"""
    
    # Calculate month boundaries
    year, month = month_year.split('-')
    start_date = date(int(year), int(month), 1)
    if int(month) == 12:
        end_date = date(int(year) + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(int(year), int(month) + 1, 1) - timedelta(days=1)
    
    # Generate monthly forecast
    monthly_forecast = engine.calculate_parallel(start_date, end_date)
    monthly_kpis = kpi_calculator.calculate_all_kpis(monthly_forecast)
    
    # Get entity breakdown for operational insights
    entity_breakdown = report_gen.generate_entity_breakdown_report()
    
    # Generate trend analysis
    trend_analysis = report_gen.generate_trend_analysis_report(monthly_forecast)
    
    # Risk assessment
    risk_assessment = report_gen.generate_risk_assessment_report(
        monthly_forecast, 
        monthly_kpis
    )
    
    # Create operations template
    ops_template = {
        "title": f"Operations Report - {month_year}",
        "sections": [
            {
                "type": "summary", 
                "title": "Monthly Performance",
                "include_kpis": True
            },
            {
                "type": "text",
                "title": "Operational Metrics",
                "content": f"""
                <div class="ops-metrics">
                    <h4>Team Composition</h4>
                    <ul>
                        <li>Total Employees: {entity_breakdown['entities_by_type'].get('employee', {}).get('count', 0)}</li>
                        <li>Monthly Payroll: ${entity_breakdown['cost_breakdown'].get('employee_costs', 0):,.0f}</li>
                        <li>Facilities Cost: ${entity_breakdown['cost_breakdown'].get('facility_costs', 0):,.0f}</li>
                    </ul>
                    
                    <h4>Revenue Streams</h4>
                    <ul>
                        <li>Grant Revenue: ${entity_breakdown['revenue_breakdown'].get('grant_revenue', 0):,.0f}</li>
                        <li>Investment: ${entity_breakdown['revenue_breakdown'].get('investment_revenue', 0):,.0f}</li>
                    </ul>
                    
                    <h4>Risk Profile</h4>
                    <ul>
                        <li>Overall Risk Score: {risk_assessment['risk_score']}/100</li>
                        <li>Cash Flow Risk: {risk_assessment['cash_flow_risks']['level'].title()}</li>
                        <li>Revenue Risk: {risk_assessment['revenue_risks']['level'].title()}</li>
                    </ul>
                </div>
                """
            },
            {
                "type": "chart",
                "title": "Monthly Financial Performance", 
                "chart_type": "line",
                "data_source": "forecast"
            },
            {
                "type": "text",
                "title": "Trends & Analysis",
                "content": f"""
                <div class="trend-analysis">
                    <h4>Revenue Trends</h4>
                    <p>Direction: {trend_analysis['revenue_trend']['trend_direction'].title()}</p>
                    <p>Monthly Change: ${trend_analysis['revenue_trend']['monthly_change']:,.0f}</p>
                    
                    <h4>Expense Trends</h4>
                    <p>Direction: {trend_analysis['expense_trend']['trend_direction'].title()}</p>
                    <p>Monthly Change: ${trend_analysis['expense_trend']['monthly_change']:,.0f}</p>
                    
                    <h4>Cash Flow Health</h4>
                    <p>Trend: {trend_analysis['cash_flow_trend']['trend_direction'].title()}</p>
                    <p>Strength: {trend_analysis['cash_flow_trend']['trend_strength']:.2f}</p>
                </div>
                """
            }
        ]
    }
    
    # Generate automated report
    automation_config = {
        "frequency": "monthly",
        "reports": ["html_report", "csv_export", "kpi_dashboard"],
        "output_format": "timestamped",
        "archive_old_reports": True
    }
    
    ops_report = report_gen.generate_custom_report(
        df=monthly_forecast,
        kpis=monthly_kpis,
        template_config=ops_template,
        filename=f"operations_report_{month_year.replace('-', '_')}.html"
    )
    
    # Generate automated package
    automated_package = report_gen.generate_automated_report(
        df=monthly_forecast,
        kpis=monthly_kpis,
        automation_config=automation_config,
        run_timestamp=datetime.now()
    )
    
    return {
        'operations_report': ops_report,
        'automated_package': automated_package,
        'risk_assessment': risk_assessment,
        'trends': trend_analysis
    }

# Generate March 2024 operations report
march_ops = generate_monthly_operations_report("2024-03")
print(f"March operations report: {march_ops['operations_report']}")
print(f"Automated package: {march_ops['automated_package']['output_directory']}")
print(f"Risk score: {march_ops['risk_assessment']['risk_score']}/100")
```

## Performance Monitoring

### Example 13: Report Generation Performance Analysis

```python
import time
from pathlib import Path

def benchmark_report_generation():
    """Benchmark different report generation methods"""
    
    # Sample data
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    forecast_df = engine.calculate_parallel(start_date, end_date)
    kpis = kpi_calculator.calculate_all_kpis(forecast_df)
    
    results = {}
    
    # Benchmark individual formats
    formats_to_test = [
        ("HTML Report", lambda: report_gen.generate_html_report(forecast_df, kpis)),
        ("Excel Export", lambda: report_gen.export_to_excel(forecast_df, kpis, "benchmark")),
        ("CSV Export", lambda: report_gen.export_to_csv(forecast_df, "benchmark")),
        ("KPI Dashboard", lambda: report_gen.generate_kpi_dashboard(kpis)),
        ("Cash Flow Chart", lambda: report_gen.generate_cash_flow_chart(forecast_df)),
        ("Complete Package", lambda: report_gen.generate_complete_report_package(forecast_df, kpis))
    ]
    
    print("=== REPORT GENERATION BENCHMARKS ===")
    for name, func in formats_to_test:
        start_time = time.time()
        try:
            result = func()
            end_time = time.time()
            duration = end_time - start_time
            
            # Get file size if applicable
            file_size = 0
            if isinstance(result, (str, Path)):
                if Path(result).exists():
                    file_size = Path(result).stat().st_size / 1024  # KB
            
            results[name] = {
                'duration': duration,
                'file_size_kb': file_size,
                'success': True
            }
            
            print(f"{name:20s}: {duration:6.2f}s, {file_size:8.1f} KB")
            
        except Exception as e:
            results[name] = {
                'duration': 0,
                'file_size_kb': 0,
                'success': False,
                'error': str(e)
            }
            print(f"{name:20s}: FAILED - {e}")
    
    return results

# Run benchmarks
benchmark_results = benchmark_report_generation()

# Analyze performance
total_time = sum(r['duration'] for r in benchmark_results.values() if r['success'])
print(f"\nTotal generation time: {total_time:.2f} seconds")
print(f"Average time per format: {total_time / len([r for r in benchmark_results.values() if r['success']]):.2f} seconds")
```

---

These examples demonstrate the full range of CashCow's reporting and analysis capabilities, from basic report generation to sophisticated risk analysis and custom dashboards. Each example can be adapted to specific business needs and integrated into automated workflows for regular reporting and analysis.