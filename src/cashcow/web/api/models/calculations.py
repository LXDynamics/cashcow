"""
CashCow Web API - Pydantic models for calculations and analytics.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


# Base models for common structures
class PeriodData(BaseModel):
    """Data for a specific time period."""
    period: str = Field(..., description="Period identifier (YYYY-MM)")
    revenue: float = Field(..., description="Total revenue for period")
    expenses: float = Field(..., description="Total expenses for period")
    net_cash_flow: float = Field(..., description="Net cash flow for period")
    cash_balance: float = Field(..., description="Cash balance at end of period")


class KPIData(BaseModel):
    """KPI metrics data."""
    name: str = Field(..., description="KPI name")
    value: Union[float, int, str] = Field(..., description="KPI value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    description: Optional[str] = Field(None, description="KPI description")
    alert_level: Optional[str] = Field(None, description="Alert level (info, warning, critical)")


class Alert(BaseModel):
    """KPI alert information."""
    level: str = Field(..., description="Alert level (info, warning, critical)")
    metric: str = Field(..., description="KPI metric name")
    message: str = Field(..., description="Alert message")
    recommendation: Optional[str] = Field(None, description="Recommended action")


# Forecast request/response models
class ForecastRequest(BaseModel):
    """Request for cash flow forecast."""
    months: int = Field(default=24, ge=1, le=120, description="Forecast period in months")
    scenario: str = Field(default="baseline", description="Scenario name to use")
    start_date: Optional[date] = Field(None, description="Start date for forecast (defaults to today)")
    include_kpis: bool = Field(default=False, description="Include KPI analysis in response")
    aggregation: str = Field(default="monthly", pattern="^(monthly|quarterly|yearly)$", description="Data aggregation level")


class ForecastResponse(BaseModel):
    """Response for cash flow forecast."""
    scenario: str = Field(..., description="Scenario used")
    start_date: date = Field(..., description="Forecast start date")
    end_date: date = Field(..., description="Forecast end date")
    periods: List[PeriodData] = Field(..., description="Period-by-period data")
    summary: Dict[str, float] = Field(..., description="Summary metrics")
    kpis: Optional[List[KPIData]] = Field(None, description="KPI analysis if requested")
    alerts: Optional[List[Alert]] = Field(None, description="KPI alerts if any")


# KPI request/response models
class KPIRequest(BaseModel):
    """Request for KPI calculation."""
    start_date: Optional[date] = Field(None, description="Start date for KPI period")
    end_date: Optional[date] = Field(None, description="End date for KPI period")
    scenario: str = Field(default="baseline", description="Scenario to use")
    include_trends: bool = Field(default=False, description="Include trend analysis")


class KPIResponse(BaseModel):
    """Response for KPI calculation."""
    calculation_date: date = Field(..., description="Date of calculation")
    period_start: date = Field(..., description="Start of analysis period")
    period_end: date = Field(..., description="End of analysis period")
    scenario: str = Field(..., description="Scenario used")
    kpis: List[KPIData] = Field(..., description="Calculated KPIs")
    alerts: List[Alert] = Field(..., description="KPI alerts")
    trends: Optional[Dict[str, List[float]]] = Field(None, description="Trend data if requested")


# Cash flow request/response models
class CashFlowRequest(BaseModel):
    """Request for cash flow data."""
    start_date: Optional[date] = Field(None, description="Start date for cash flow data")
    end_date: Optional[date] = Field(None, description="End date for cash flow data")
    scenario: str = Field(default="baseline", description="Scenario to use")
    aggregation: str = Field(default="monthly", pattern="^(monthly|quarterly|yearly)$", description="Data aggregation level")
    breakdown: bool = Field(default=False, description="Include revenue/expense breakdown by category")


class CashFlowBreakdown(BaseModel):
    """Breakdown of cash flow by category."""
    period: str = Field(..., description="Period identifier")
    revenue_breakdown: Dict[str, float] = Field(..., description="Revenue by category")
    expense_breakdown: Dict[str, float] = Field(..., description="Expenses by category")


class CashFlowResponse(BaseModel):
    """Response for cash flow data."""
    scenario: str = Field(..., description="Scenario used")
    start_date: date = Field(..., description="Data start date")
    end_date: date = Field(..., description="Data end date")
    aggregation: str = Field(..., description="Data aggregation level")
    periods: List[PeriodData] = Field(..., description="Cash flow data by period")
    breakdown: Optional[List[CashFlowBreakdown]] = Field(None, description="Category breakdown if requested")
    summary: Dict[str, float] = Field(..., description="Summary metrics")


# Scenario validation models
class ScenarioValidationRequest(BaseModel):
    """Request to validate a scenario."""
    scenario_name: str = Field(..., description="Name of scenario to validate")
    check_entities: bool = Field(default=True, description="Validate entity compatibility")
    check_assumptions: bool = Field(default=True, description="Validate scenario assumptions")


class ValidationIssue(BaseModel):
    """Validation issue found in scenario."""
    level: str = Field(..., description="Issue level (error, warning, info)")
    entity_name: Optional[str] = Field(None, description="Entity name if entity-specific")
    field: Optional[str] = Field(None, description="Field name if field-specific")
    message: str = Field(..., description="Issue description")
    suggestion: Optional[str] = Field(None, description="Suggested fix")


class ScenarioValidationResponse(BaseModel):
    """Response for scenario validation."""
    scenario_name: str = Field(..., description="Scenario validated")
    valid: bool = Field(..., description="Whether scenario is valid")
    issues: List[ValidationIssue] = Field(..., description="Validation issues found")
    entities_affected: int = Field(..., description="Number of entities affected by scenario")
    summary: Dict[str, Any] = Field(..., description="Validation summary")


# Scenario management models
class ScenarioInfo(BaseModel):
    """Information about a scenario."""
    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Scenario description")
    assumptions: Dict[str, Any] = Field(..., description="Scenario assumptions")
    entity_overrides: int = Field(..., description="Number of entity overrides")
    entity_filters: Dict[str, Any] = Field(..., description="Entity filters")
    created_date: Optional[date] = Field(None, description="Creation date")


class ScenarioListResponse(BaseModel):
    """Response listing available scenarios."""
    scenarios: List[ScenarioInfo] = Field(..., description="Available scenarios")
    default_scenario: str = Field(..., description="Default scenario name")


class ScenarioCompareRequest(BaseModel):
    """Request to compare multiple scenarios."""
    scenario_names: List[str] = Field(..., min_items=2, max_items=5, description="Scenarios to compare")
    months: int = Field(default=24, ge=1, le=120, description="Forecast period in months")
    start_date: Optional[date] = Field(None, description="Start date for comparison")
    metrics: List[str] = Field(
        default=["total_revenue", "total_expenses", "net_cash_flow", "cash_balance"], 
        description="Metrics to compare"
    )


class ScenarioComparison(BaseModel):
    """Comparison data for a specific metric across scenarios."""
    metric: str = Field(..., description="Metric name")
    scenarios: Dict[str, List[float]] = Field(..., description="Scenario data by name")
    summary: Dict[str, Dict[str, float]] = Field(..., description="Summary stats by scenario")


class ScenarioCompareResponse(BaseModel):
    """Response for scenario comparison."""
    scenarios: List[str] = Field(..., description="Scenarios compared")
    start_date: date = Field(..., description="Comparison start date")
    end_date: date = Field(..., description="Comparison end date")
    comparisons: List[ScenarioComparison] = Field(..., description="Metric comparisons")
    winner: Dict[str, str] = Field(..., description="Best scenario by metric")


# What-if analysis models
class ParameterAdjustment(BaseModel):
    """Parameter adjustment for what-if analysis."""
    entity_type: Optional[str] = Field(None, description="Entity type to adjust (optional)")
    entity_name: Optional[str] = Field(None, description="Specific entity name (optional)")
    field: str = Field(..., description="Field to adjust")
    adjustment_type: str = Field(..., pattern="^(multiply|add|set)$", description="Type of adjustment")
    value: float = Field(..., description="Adjustment value")
    description: Optional[str] = Field(None, description="Description of adjustment")


class WhatIfRequest(BaseModel):
    """Request for what-if analysis."""
    base_scenario: str = Field(default="baseline", description="Base scenario to modify")
    adjustments: List[ParameterAdjustment] = Field(..., min_items=1, description="Parameter adjustments")
    months: int = Field(default=24, ge=1, le=120, description="Analysis period in months")
    start_date: Optional[date] = Field(None, description="Start date for analysis")
    name: Optional[str] = Field(None, description="Name for this what-if scenario")


class WhatIfResponse(BaseModel):
    """Response for what-if analysis."""
    base_scenario: str = Field(..., description="Base scenario used")
    scenario_name: str = Field(..., description="What-if scenario name")
    adjustments: List[ParameterAdjustment] = Field(..., description="Adjustments applied")
    baseline_forecast: ForecastResponse = Field(..., description="Baseline forecast")
    adjusted_forecast: ForecastResponse = Field(..., description="Adjusted forecast")
    impact_summary: Dict[str, float] = Field(..., description="Impact summary (differences)")


# Monte Carlo analysis models
class MonteCarloRequest(BaseModel):
    """Request for Monte Carlo simulation."""
    scenario: str = Field(default="baseline", description="Base scenario for simulation")
    iterations: int = Field(default=1000, ge=100, le=10000, description="Number of simulation iterations")
    months: int = Field(default=24, ge=1, le=120, description="Simulation period in months")
    start_date: Optional[date] = Field(None, description="Start date for simulation")
    uncertainty_params: Optional[Dict[str, Dict[str, float]]] = Field(
        None, 
        description="Custom uncertainty parameters (param_name -> {type, mean, std, min, max})"
    )
    confidence_levels: List[float] = Field(
        default=[0.1, 0.25, 0.5, 0.75, 0.9], 
        description="Confidence levels for percentile analysis"
    )


class MonteCarloMetrics(BaseModel):
    """Monte Carlo simulation metrics."""
    metric: str = Field(..., description="Metric name")
    mean: float = Field(..., description="Mean value across iterations")
    std: float = Field(..., description="Standard deviation")
    min: float = Field(..., description="Minimum value")
    max: float = Field(..., description="Maximum value")
    percentiles: Dict[str, float] = Field(..., description="Percentile values")


class MonteCarloResponse(BaseModel):
    """Response for Monte Carlo simulation."""
    scenario: str = Field(..., description="Base scenario used")
    iterations: int = Field(..., description="Number of iterations run")
    start_date: date = Field(..., description="Simulation start date")
    end_date: date = Field(..., description="Simulation end date")
    metrics: List[MonteCarloMetrics] = Field(..., description="Simulation metrics")
    success_probability: float = Field(..., description="Probability of positive cash flow")
    risk_metrics: Dict[str, float] = Field(..., description="Risk assessment metrics")
    job_id: Optional[str] = Field(None, description="Job ID for long-running simulations")


# Sensitivity analysis models
class SensitivityRequest(BaseModel):
    """Request for sensitivity analysis."""
    scenario: str = Field(default="baseline", description="Base scenario for analysis")
    variable: str = Field(..., description="Variable to analyze sensitivity for")
    variable_range: Dict[str, float] = Field(
        ..., 
        description="Range for variable (min, max, step)"
    )
    target_metric: str = Field(
        default="net_cash_flow", 
        description="Target metric to measure sensitivity"
    )
    months: int = Field(default=24, ge=1, le=120, description="Analysis period in months")
    start_date: Optional[date] = Field(None, description="Start date for analysis")


class SensitivityPoint(BaseModel):
    """Single point in sensitivity analysis."""
    variable_value: float = Field(..., description="Variable value")
    metric_value: float = Field(..., description="Resulting metric value")
    cash_balance: float = Field(..., description="Final cash balance")


class SensitivityResponse(BaseModel):
    """Response for sensitivity analysis."""
    scenario: str = Field(..., description="Base scenario used")
    variable: str = Field(..., description="Variable analyzed")
    target_metric: str = Field(..., description="Target metric measured")
    start_date: date = Field(..., description="Analysis start date")
    end_date: date = Field(..., description="Analysis end date")
    data_points: List[SensitivityPoint] = Field(..., description="Sensitivity data points")
    elasticity: float = Field(..., description="Elasticity measure (% change in metric / % change in variable)")
    break_even_value: Optional[float] = Field(None, description="Variable value at break-even")


# Analysis job management models
class AnalysisJobStatus(BaseModel):
    """Status of a long-running analysis job."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status (queued, running, completed, failed)")
    progress: float = Field(..., ge=0.0, le=1.0, description="Job progress (0-1)")
    created_at: str = Field(..., description="Job creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    result_available: bool = Field(..., description="Whether result is available")


class AnalysisJobResponse(BaseModel):
    """Response for analysis job status."""
    job_status: AnalysisJobStatus = Field(..., description="Job status information")
    result: Optional[Union[MonteCarloResponse, SensitivityResponse]] = Field(
        None, 
        description="Analysis result if completed"
    )


# Note: Scenario name validation is handled at the API level