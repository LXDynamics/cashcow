"""
CashCow Web API - Scenarios router for scenario management and comparison.
"""

import asyncio
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

# Import CashCow modules
from cashcow.engine import CashFlowEngine, ScenarioManager, create_scenario_summary
from cashcow.storage.database import EntityStore

# Import API models
from ..models.calculations import (
    ScenarioInfo, ScenarioListResponse,
    ScenarioCompareRequest, ScenarioCompareResponse, ScenarioComparison,
    WhatIfRequest, WhatIfResponse, ParameterAdjustment,
    ForecastResponse, PeriodData
)
from ..dependencies import get_entity_loader, get_current_user

# Create router
router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def get_scenario_manager(loader=Depends(get_entity_loader)):
    """Dependency to provide ScenarioManager with loaded entities."""
    # Create EntityStore and load entities
    store = EntityStore()
    entities_dir = Path("entities")
    
    if not entities_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entities directory found. Create some entities first."
        )
    
    # Load entities
    asyncio.run(store.sync_from_yaml(entities_dir))
    
    # Create engine and scenario manager
    engine = CashFlowEngine(store)
    scenario_mgr = ScenarioManager(store, engine)
    
    # Load scenarios from scenarios directory if it exists
    scenarios_dir = Path("scenarios")
    if scenarios_dir.exists():
        scenario_mgr.load_scenarios_from_directory(scenarios_dir)
    
    return scenario_mgr


@router.get("/", response_model=ScenarioListResponse)
async def list_scenarios(
    scenario_mgr: ScenarioManager = Depends(get_scenario_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    List all available scenarios with their information.
    """
    try:
        scenario_names = scenario_mgr.list_scenarios()
        scenarios = []
        
        for name in scenario_names:
            scenario = scenario_mgr.get_scenario(name)
            if scenario:
                scenario_info = ScenarioInfo(
                    name=scenario.name,
                    description=scenario.description,
                    assumptions=scenario.assumptions,
                    entity_overrides=len(scenario.entity_overrides),
                    entity_filters=scenario.entity_filters,
                    created_date=None  # Could be added to Scenario class
                )
                scenarios.append(scenario_info)
        
        return ScenarioListResponse(
            scenarios=scenarios,
            default_scenario="baseline"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scenarios: {str(e)}"
        )


@router.get("/{scenario_id}/details", response_model=ScenarioInfo)
async def get_scenario_details(
    scenario_id: str,
    scenario_mgr: ScenarioManager = Depends(get_scenario_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific scenario.
    """
    try:
        scenario = scenario_mgr.get_scenario(scenario_id)
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario '{scenario_id}' not found"
            )
        
        return ScenarioInfo(
            name=scenario.name,
            description=scenario.description,
            assumptions=scenario.assumptions,
            entity_overrides=len(scenario.entity_overrides),
            entity_filters=scenario.entity_filters,
            created_date=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scenario details: {str(e)}"
        )


@router.post("/compare", response_model=ScenarioCompareResponse)
async def compare_scenarios(
    request: ScenarioCompareRequest,
    scenario_mgr: ScenarioManager = Depends(get_scenario_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Compare multiple scenarios side by side.
    """
    try:
        # Validate all scenarios exist
        for scenario_name in request.scenario_names:
            if not scenario_mgr.get_scenario(scenario_name):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Scenario '{scenario_name}' not found"
                )
        
        # Setup dates
        start_date = request.start_date or date.today()
        end_date = start_date + timedelta(days=request.months * 30)
        
        # Calculate results for all scenarios
        scenario_results = scenario_mgr.compare_scenarios(
            request.scenario_names, start_date, end_date
        )
        
        # Prepare comparison data
        comparisons = []
        winner = {}
        
        for metric in request.metrics:
            if metric not in ['total_revenue', 'total_expenses', 'net_cash_flow', 'cash_balance']:
                continue
            
            metric_data = {}
            metric_summary = {}
            best_value = None
            best_scenario = None
            
            for scenario_name, df in scenario_results.items():
                if len(df) == 0:
                    metric_data[scenario_name] = []
                    metric_summary[scenario_name] = {"total": 0, "average": 0, "final": 0}
                    continue
                
                # Extract metric values
                if metric == "cash_balance":
                    values = df[metric].tolist()
                    total = df[metric].iloc[-1]  # Final balance
                    average = df[metric].mean()
                    final = df[metric].iloc[-1]
                else:
                    values = df[metric].tolist()
                    total = df[metric].sum()
                    average = df[metric].mean()
                    final = df[metric].iloc[-1] if len(df) > 0 else 0
                
                metric_data[scenario_name] = values
                metric_summary[scenario_name] = {
                    "total": total,
                    "average": average,
                    "final": final
                }
                
                # Determine best scenario for this metric
                compare_value = total if metric != "cash_balance" else final
                if metric == "total_expenses":
                    # Lower is better for expenses
                    if best_value is None or compare_value < best_value:
                        best_value = compare_value
                        best_scenario = scenario_name
                else:
                    # Higher is better for revenue, cash flow, balance
                    if best_value is None or compare_value > best_value:
                        best_value = compare_value
                        best_scenario = scenario_name
            
            comparison = ScenarioComparison(
                metric=metric,
                scenarios=metric_data,
                summary=metric_summary
            )
            comparisons.append(comparison)
            
            if best_scenario:
                winner[metric] = best_scenario
        
        return ScenarioCompareResponse(
            scenarios=request.scenario_names,
            start_date=start_date,
            end_date=end_date,
            comparisons=comparisons,
            winner=winner
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare scenarios: {str(e)}"
        )


@router.post("/what-if", response_model=WhatIfResponse)
async def analyze_what_if(
    request: WhatIfRequest,
    scenario_mgr: ScenarioManager = Depends(get_scenario_manager),
    current_user: dict = Depends(get_current_user)
):
    """
    Perform what-if analysis by adjusting parameters on a base scenario.
    """
    try:
        # Validate base scenario exists
        base_scenario = scenario_mgr.get_scenario(request.base_scenario)
        if not base_scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Base scenario '{request.base_scenario}' not found"
            )
        
        # Setup dates
        start_date = request.start_date or date.today()
        end_date = start_date + timedelta(days=request.months * 30)
        
        # Calculate baseline forecast
        baseline_df = scenario_mgr.calculate_scenario(request.base_scenario, start_date, end_date)
        baseline_forecast = _dataframe_to_forecast_response(
            baseline_df, request.base_scenario, start_date, end_date
        )
        
        # Create temporary what-if scenario
        from cashcow.engine.scenarios import Scenario
        
        # Start with base scenario data
        whatif_scenario = Scenario(
            name=request.name or f"whatif_{request.base_scenario}",
            description=f"What-if analysis based on {request.base_scenario}",
            assumptions=base_scenario.assumptions.copy(),
            entity_overrides=base_scenario.entity_overrides.copy(),
            entity_filters=base_scenario.entity_filters.copy()
        )
        
        # Apply adjustments
        for adjustment in request.adjustments:
            override = _create_override_from_adjustment(adjustment)
            whatif_scenario.entity_overrides.append(override)
        
        # Add temporary scenario to manager
        scenario_mgr.add_scenario(whatif_scenario)
        
        try:
            # Calculate what-if forecast
            whatif_df = scenario_mgr.calculate_scenario(whatif_scenario.name, start_date, end_date)
            whatif_forecast = _dataframe_to_forecast_response(
                whatif_df, whatif_scenario.name, start_date, end_date
            )
            
            # Calculate impact summary (differences)
            impact_summary = {
                "revenue_change": whatif_df['total_revenue'].sum() - baseline_df['total_revenue'].sum(),
                "expense_change": whatif_df['total_expenses'].sum() - baseline_df['total_expenses'].sum(),
                "cash_flow_change": whatif_df['net_cash_flow'].sum() - baseline_df['net_cash_flow'].sum(),
                "final_balance_change": (whatif_df['cash_balance'].iloc[-1] - baseline_df['cash_balance'].iloc[-1]) if len(whatif_df) > 0 and len(baseline_df) > 0 else 0
            }
            
            return WhatIfResponse(
                base_scenario=request.base_scenario,
                scenario_name=whatif_scenario.name,
                adjustments=request.adjustments,
                baseline_forecast=baseline_forecast,
                adjusted_forecast=whatif_forecast,
                impact_summary=impact_summary
            )
            
        finally:
            # Remove temporary scenario
            if whatif_scenario.name in scenario_mgr.scenarios:
                del scenario_mgr.scenarios[whatif_scenario.name]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform what-if analysis: {str(e)}"
        )


# Helper functions

def _dataframe_to_forecast_response(df, scenario_name: str, start_date: date, end_date: date) -> ForecastResponse:
    """Convert DataFrame to ForecastResponse."""
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
    
    # Calculate summary
    summary = {
        "total_revenue": df['total_revenue'].sum(),
        "total_expenses": df['total_expenses'].sum(),
        "net_cash_flow": df['net_cash_flow'].sum(),
        "final_cash_balance": df['cash_balance'].iloc[-1] if len(df) > 0 else 0.0,
        "peak_revenue": df['total_revenue'].max(),
        "peak_expenses": df['total_expenses'].max(),
        "average_monthly_burn": -df[df['net_cash_flow'] < 0]['net_cash_flow'].mean() if len(df) > 0 else 0.0
    }
    
    return ForecastResponse(
        scenario=scenario_name,
        start_date=start_date,
        end_date=end_date,
        periods=periods,
        summary=summary,
        kpis=None,
        alerts=None
    )


def _create_override_from_adjustment(adjustment: ParameterAdjustment) -> Dict:
    """Create scenario override from parameter adjustment."""
    override = {
        'field': adjustment.field
    }
    
    # Add entity matching criteria
    if adjustment.entity_type:
        override['entity_type'] = adjustment.entity_type
    if adjustment.entity_name:
        override['entity'] = adjustment.entity_name
    
    # Add adjustment based on type
    if adjustment.adjustment_type == "multiply":
        override['multiplier'] = adjustment.value
    elif adjustment.adjustment_type == "add":
        # For add, we need to modify the field directly
        # This is simplified - in production might need more complex logic
        override['value'] = adjustment.value  # This would need field-specific handling
    elif adjustment.adjustment_type == "set":
        override['value'] = adjustment.value
    
    return override