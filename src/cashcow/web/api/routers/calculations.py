"""
CashCow Web API - Calculations router for forecasts, KPIs, and cash flow analysis.
"""

import asyncio
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse

# Import CashCow modules
from cashcow.engine import CashFlowEngine, KPICalculator, ScenarioManager
from cashcow.storage.database import EntityStore

# Import API models
from ..models.calculations import (
    ForecastRequest, ForecastResponse, PeriodData,
    KPIRequest, KPIResponse, KPIData, Alert,
    CashFlowRequest, CashFlowResponse, CashFlowBreakdown,
    ScenarioValidationRequest, ScenarioValidationResponse, ValidationIssue
)
from ..dependencies import get_entity_loader, get_current_user
from ..exceptions import EntityNotFoundError

# Create router
router = APIRouter(prefix="/calculations", tags=["calculations"])


def get_cashflow_engine(loader=Depends(get_entity_loader)):
    """Dependency to provide CashFlow engine with loaded entities."""
    # Create EntityStore and load entities
    store = EntityStore()
    entities_dir = Path("entities")
    
    if not entities_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entities directory found. Create some entities first."
        )
    
    # Load entities synchronously for now
    # In production, consider async loading
    asyncio.run(store.sync_from_yaml(entities_dir))
    
    # Create and return engine
    return CashFlowEngine(store)


def get_scenario_manager(engine: CashFlowEngine = Depends(get_cashflow_engine)):
    """Dependency to provide ScenarioManager."""
    # Get store from engine (a bit hacky, but works)
    store = engine._store if hasattr(engine, '_store') else EntityStore()
    
    # Create scenario manager
    scenario_mgr = ScenarioManager(store, engine)
    
    # Load scenarios from scenarios directory if it exists
    scenarios_dir = Path("scenarios")
    if scenarios_dir.exists():
        scenario_mgr.load_scenarios_from_directory(scenarios_dir)
    
    return scenario_mgr


@router.post("/forecast", response_model=ForecastResponse)
async def calculate_forecast(
    request: ForecastRequest,
    engine: CashFlowEngine = Depends(get_cashflow_engine),
    scenario_mgr: ScenarioManager = Depends(get_scenario_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate cash flow forecast for specified period and scenario.
    """
    try:
        # Setup dates
        start_date = request.start_date or date.today()
        end_date = start_date + timedelta(days=request.months * 30)
        
        # Calculate forecast based on scenario
        if request.scenario == "baseline":
            df = engine.calculate_parallel(start_date, end_date)
        else:
            # Check if scenario exists
            if not scenario_mgr.get_scenario(request.scenario):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Scenario '{request.scenario}' not found"
                )
            df = scenario_mgr.calculate_scenario(request.scenario, start_date, end_date)
        
        # Convert DataFrame to period data
        periods = []
        for _, row in df.iterrows():
            period_data = PeriodData(
                period=row['period'],
                revenue=row['total_revenue'],
                expenses=row['total_expenses'],
                net_cash_flow=row['net_cash_flow'],
                cash_balance=row['cash_balance']
            )
            periods.append(period_data)
        
        # Apply aggregation if requested
        if request.aggregation != "monthly":
            periods = _aggregate_periods(periods, request.aggregation)
        
        # Calculate summary metrics
        summary = {
            "total_revenue": df['total_revenue'].sum(),
            "total_expenses": df['total_expenses'].sum(),
            "net_cash_flow": df['net_cash_flow'].sum(),
            "final_cash_balance": df['cash_balance'].iloc[-1] if len(df) > 0 else 0.0,
            "peak_revenue": df['total_revenue'].max(),
            "peak_expenses": df['total_expenses'].max(),
            "average_monthly_burn": -df[df['net_cash_flow'] < 0]['net_cash_flow'].mean() if len(df) > 0 else 0.0
        }
        
        # Calculate KPIs if requested
        kpis = None
        alerts = None
        if request.include_kpis:
            kpi_calc = KPICalculator()
            kpi_results = kpi_calc.calculate_all_kpis(df)
            
            # Convert KPIs to response format
            kpis = []
            for kpi_name, kpi_value in kpi_results.items():
                kpi_data = KPIData(
                    name=kpi_name,
                    value=kpi_value,
                    unit=_get_kpi_unit(kpi_name),
                    description=_get_kpi_description(kpi_name)
                )
                kpis.append(kpi_data)
            
            # Get alerts
            alert_results = kpi_calc.get_kpi_alerts(kpi_results)
            alerts = []
            for alert in alert_results:
                alert_data = Alert(
                    level=alert['level'],
                    metric=alert['metric'],
                    message=alert['message'],
                    recommendation=alert.get('recommendation')
                )
                alerts.append(alert_data)
        
        return ForecastResponse(
            scenario=request.scenario,
            start_date=start_date,
            end_date=end_date,
            periods=periods,
            summary=summary,
            kpis=kpis,
            alerts=alerts
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate forecast: {str(e)}"
        )


@router.get("/kpis", response_model=KPIResponse)
async def calculate_kpis(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    scenario: str = "baseline",
    include_trends: bool = False,
    engine: CashFlowEngine = Depends(get_cashflow_engine),
    scenario_mgr: ScenarioManager = Depends(get_scenario_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate KPI metrics for specified period and scenario.
    """
    try:
        # Setup default dates
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=12 * 30)  # 12 months
        
        # Calculate cash flow for KPI analysis
        if scenario == "baseline":
            df = engine.calculate_parallel(start_date, end_date)
        else:
            if not scenario_mgr.get_scenario(scenario):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Scenario '{scenario}' not found"
                )
            df = scenario_mgr.calculate_scenario(scenario, start_date, end_date)
        
        # Calculate KPIs
        kpi_calc = KPICalculator()
        kpi_results = kpi_calc.calculate_all_kpis(df)
        
        # Convert KPIs to response format
        kpis = []
        for kpi_name, kpi_value in kpi_results.items():
            # Determine alert level
            alert_level = _get_kpi_alert_level(kpi_name, kpi_value)
            
            kpi_data = KPIData(
                name=kpi_name,
                value=kpi_value,
                unit=_get_kpi_unit(kpi_name),
                description=_get_kpi_description(kpi_name),
                alert_level=alert_level
            )
            kpis.append(kpi_data)
        
        # Get alerts
        alert_results = kpi_calc.get_kpi_alerts(kpi_results)
        alerts = []
        for alert in alert_results:
            alert_data = Alert(
                level=alert['level'],
                metric=alert['metric'],
                message=alert['message'],
                recommendation=alert.get('recommendation')
            )
            alerts.append(alert_data)
        
        # Calculate trends if requested
        trends = None
        if include_trends and len(df) >= 3:
            trend_df = kpi_calc.calculate_kpi_trends(df)
            trends = {
                "revenue_trend": trend_df['revenue_trend'].tolist(),
                "expense_trend": trend_df['expense_trend'].tolist(),
                "burn_trend": trend_df['burn_trend'].tolist()
            }
        
        return KPIResponse(
            calculation_date=date.today(),
            period_start=start_date,
            period_end=end_date,
            scenario=scenario,
            kpis=kpis,
            alerts=alerts,
            trends=trends
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate KPIs: {str(e)}"
        )


@router.get("/cashflow", response_model=CashFlowResponse)
async def get_cashflow_data(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    scenario: str = "baseline",
    aggregation: str = "monthly",
    breakdown: bool = False,
    engine: CashFlowEngine = Depends(get_cashflow_engine),
    scenario_mgr: ScenarioManager = Depends(get_scenario_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Get cash flow data with optional breakdown by category.
    """
    try:
        # Setup default dates
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=24 * 30)  # 24 months
        
        # Calculate cash flow
        if scenario == "baseline":
            df = engine.calculate_parallel(start_date, end_date)
        else:
            if not scenario_mgr.get_scenario(scenario):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Scenario '{scenario}' not found"
                )
            df = scenario_mgr.calculate_scenario(scenario, start_date, end_date)
        
        # Convert to period data
        periods = []
        for _, row in df.iterrows():
            period_data = PeriodData(
                period=row['period'],
                revenue=row['total_revenue'],
                expenses=row['total_expenses'],
                net_cash_flow=row['net_cash_flow'],
                cash_balance=row['cash_balance']
            )
            periods.append(period_data)
        
        # Apply aggregation if requested
        if aggregation != "monthly":
            periods = _aggregate_periods(periods, aggregation)
        
        # Create breakdown if requested
        breakdown_data = None
        if breakdown:
            breakdown_data = []
            revenue_cols = [col for col in df.columns if col.endswith('_revenue')]
            expense_cols = [col for col in df.columns if col.endswith('_costs') or col.endswith('_expenses')]
            
            for _, row in df.iterrows():
                revenue_breakdown = {col.replace('_revenue', ''): row[col] for col in revenue_cols if col in row}
                expense_breakdown = {col.replace('_costs', '').replace('_expenses', ''): row[col] for col in expense_cols if col in row}
                
                breakdown_item = CashFlowBreakdown(
                    period=row['period'],
                    revenue_breakdown=revenue_breakdown,
                    expense_breakdown=expense_breakdown
                )
                breakdown_data.append(breakdown_item)
        
        # Calculate summary
        summary = {
            "total_revenue": df['total_revenue'].sum(),
            "total_expenses": df['total_expenses'].sum(),
            "net_cash_flow": df['net_cash_flow'].sum(),
            "final_cash_balance": df['cash_balance'].iloc[-1] if len(df) > 0 else 0.0,
            "periods_profitable": (df['net_cash_flow'] > 0).sum(),
            "average_monthly_revenue": df['total_revenue'].mean(),
            "average_monthly_expenses": df['total_expenses'].mean()
        }
        
        return CashFlowResponse(
            scenario=scenario,
            start_date=start_date,
            end_date=end_date,
            aggregation=aggregation,
            periods=periods,
            breakdown=breakdown_data,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cash flow data: {str(e)}"
        )


@router.post("/validate-scenario", response_model=ScenarioValidationResponse)
async def validate_scenario(
    request: ScenarioValidationRequest,
    scenario_mgr: ScenarioManager = Depends(get_scenario_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Validate a scenario and check for potential issues.
    """
    try:
        scenario = scenario_mgr.get_scenario(request.scenario_name)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario '{request.scenario_name}' not found"
            )
        
        issues = []
        entities_affected = 0
        
        if request.check_entities:
            # Get all entities and apply scenario to validate
            store = scenario_mgr.store
            entities = store.query()
            
            for entity in entities:
                try:
                    if scenario.should_include_entity(entity):
                        entities_affected += 1
                        modified_entity = scenario.apply_to_entity(entity)
                        
                        # Basic validation checks
                        entity_dict = modified_entity.to_dict()
                        
                        # Check for negative values where they shouldn't be
                        financial_fields = ['salary', 'amount', 'monthly_cost', 'cost']
                        for field in financial_fields:
                            if field in entity_dict and entity_dict[field] < 0:
                                issues.append(ValidationIssue(
                                    level="error",
                                    entity_name=entity.name,
                                    field=field,
                                    message=f"Scenario results in negative {field}: {entity_dict[field]}",
                                    suggestion=f"Adjust scenario overrides for {field}"
                                ))
                        
                        # Check for unrealistic values
                        if 'salary' in entity_dict and entity_dict['salary'] > 500000:
                            issues.append(ValidationIssue(
                                level="warning",
                                entity_name=entity.name,
                                field="salary",
                                message=f"Very high salary after scenario: ${entity_dict['salary']:,.0f}",
                                suggestion="Review salary multipliers in scenario"
                            ))
                        
                except Exception as e:
                    issues.append(ValidationIssue(
                        level="error",
                        entity_name=entity.name,
                        field=None,
                        message=f"Failed to apply scenario: {str(e)}",
                        suggestion="Check scenario overrides for this entity"
                    ))
        
        if request.check_assumptions:
            # Validate scenario assumptions
            assumptions = scenario.assumptions
            
            # Check for reasonable ranges
            if 'revenue_growth_rate' in assumptions:
                growth_rate = assumptions['revenue_growth_rate']
                if growth_rate < -0.5 or growth_rate > 2.0:
                    issues.append(ValidationIssue(
                        level="warning",
                        entity_name=None,
                        field="revenue_growth_rate",
                        message=f"Extreme revenue growth rate: {growth_rate:.1%}",
                        suggestion="Consider more realistic growth assumptions"
                    ))
            
            if 'overhead_multiplier' in assumptions:
                multiplier = assumptions['overhead_multiplier']
                if multiplier < 1.0 or multiplier > 3.0:
                    issues.append(ValidationIssue(
                        level="warning",
                        entity_name=None,
                        field="overhead_multiplier",
                        message=f"Unusual overhead multiplier: {multiplier}",
                        suggestion="Typical range is 1.1 to 2.5"
                    ))
        
        # Summary
        error_count = len([i for i in issues if i.level == "error"])
        warning_count = len([i for i in issues if i.level == "warning"])
        
        summary = {
            "total_issues": len(issues),
            "errors": error_count,
            "warnings": warning_count,
            "entities_processed": len(entities) if request.check_entities else 0,
            "entities_affected": entities_affected,
            "has_assumptions": len(scenario.assumptions) > 0,
            "has_overrides": len(scenario.entity_overrides) > 0
        }
        
        return ScenarioValidationResponse(
            scenario_name=request.scenario_name,
            valid=error_count == 0,
            issues=issues,
            entities_affected=entities_affected,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate scenario: {str(e)}"
        )


# Helper functions

def _aggregate_periods(periods: List[PeriodData], aggregation: str) -> List[PeriodData]:
    """Aggregate period data by quarter or year."""
    if aggregation == "monthly":
        return periods
    
    aggregated = []
    current_group = []
    
    for i, period in enumerate(periods):
        current_group.append(period)
        
        # Determine if we should close current group
        should_close = False
        if aggregation == "quarterly":
            should_close = (i + 1) % 3 == 0 or i == len(periods) - 1
        elif aggregation == "yearly":
            should_close = (i + 1) % 12 == 0 or i == len(periods) - 1
        
        if should_close and current_group:
            # Aggregate the group
            total_revenue = sum(p.revenue for p in current_group)
            total_expenses = sum(p.expenses for p in current_group)
            total_net_flow = sum(p.net_cash_flow for p in current_group)
            final_balance = current_group[-1].cash_balance
            
            # Create period identifier
            first_period = current_group[0].period
            last_period = current_group[-1].period
            if aggregation == "quarterly":
                period_id = f"Q{((i // 3) + 1)}-{first_period[:4]}"
            else:  # yearly
                period_id = first_period[:4]
            
            aggregated_period = PeriodData(
                period=period_id,
                revenue=total_revenue,
                expenses=total_expenses,
                net_cash_flow=total_net_flow,
                cash_balance=final_balance
            )
            aggregated.append(aggregated_period)
            current_group = []
    
    return aggregated


def _get_kpi_unit(kpi_name: str) -> Optional[str]:
    """Get appropriate unit for KPI display."""
    if "rate" in kpi_name or "percentage" in kpi_name or "growth" in kpi_name:
        return "%"
    elif "months" in kpi_name:
        return "months"
    elif "amount" in kpi_name or "revenue" in kpi_name or "cost" in kpi_name or "burn" in kpi_name:
        return "$"
    elif "efficiency" in kpi_name or "ratio" in kpi_name:
        return "ratio"
    else:
        return None


def _get_kpi_description(kpi_name: str) -> Optional[str]:
    """Get description for KPI."""
    descriptions = {
        "runway_months": "Months of cash remaining at current burn rate",
        "burn_rate": "Average monthly cash consumption",
        "revenue_growth_rate": "Monthly revenue growth rate",
        "cash_efficiency": "Revenue generated per dollar of cash consumed",
        "employee_cost_efficiency": "Revenue per dollar of employee costs",
        "revenue_per_employee": "Average revenue per employee",
        "rd_percentage": "R&D spending as percentage of total expenses",
        "cash_flow_volatility": "Standard deviation of monthly cash flow",
        "revenue_diversification": "Measure of revenue source diversification (higher is better)"
    }
    return descriptions.get(kpi_name)


def _get_kpi_alert_level(kpi_name: str, value: float) -> Optional[str]:
    """Determine alert level for a KPI value."""
    if kpi_name == "runway_months":
        if value < 3:
            return "critical"
        elif value < 6:
            return "warning"
    elif kpi_name == "burn_rate" and value > 100000:
        return "warning"
    elif kpi_name == "revenue_concentration_risk" and value > 0.8:
        return "warning"
    elif kpi_name == "cash_flow_risk" and value > 2.0:
        return "info"
    
    return None