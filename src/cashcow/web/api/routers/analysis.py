"""
CashCow Web API - Analysis router for Monte Carlo simulations and sensitivity analysis.
"""

import asyncio
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse

# Import CashCow modules
from cashcow.engine import CashFlowEngine
from cashcow.storage.database import EntityStore
from cashcow.analysis import MonteCarloSimulator, Distribution, UncertaintyModel, create_common_uncertainties
from cashcow.analysis import WhatIfAnalyzer, Parameter

# Import API models
from ..models.calculations import (
    MonteCarloRequest, MonteCarloResponse, MonteCarloMetrics,
    SensitivityRequest, SensitivityResponse, SensitivityPoint,
    AnalysisJobStatus, AnalysisJobResponse
)
from ..dependencies import get_entity_loader, get_current_user

# Create router
router = APIRouter(prefix="/analysis", tags=["analysis"])

# In-memory job storage (in production, use Redis or database)
analysis_jobs: Dict[str, Dict] = {}


def get_analysis_components(loader=Depends(get_entity_loader)):
    """Dependency to provide analysis components."""
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
    
    # Create components
    engine = CashFlowEngine(store)
    monte_carlo = MonteCarloSimulator(engine, store)
    whatif_analyzer = WhatIfAnalyzer(engine, store)
    
    return {
        "store": store,
        "engine": engine,
        "monte_carlo": monte_carlo,
        "whatif_analyzer": whatif_analyzer
    }


@router.post("/monte-carlo", response_model=MonteCarloResponse)
async def run_monte_carlo_simulation(
    request: MonteCarloRequest,
    background_tasks: BackgroundTasks,
    components: dict = Depends(get_analysis_components),
    current_user: dict = Depends(get_current_user)
):
    """
    Run Monte Carlo simulation for cash flow analysis.
    """
    try:
        # Setup dates
        start_date = request.start_date or date.today()
        end_date = start_date + timedelta(days=request.months * 30)
        
        monte_carlo = components["monte_carlo"]
        
        # Add uncertainties
        if request.uncertainty_params:
            # Custom uncertainties
            for param_name, uncertainty_config in request.uncertainty_params.items():
                dist_type = uncertainty_config.get("type", "normal")
                dist_params = {k: v for k, v in uncertainty_config.items() if k != "type"}
                
                distribution = Distribution(dist_type, dist_params)
                
                # Parse parameter name to extract entity info
                parts = param_name.split("_")
                if len(parts) >= 3:
                    entity_type = parts[0]
                    field = parts[-1]
                    entity_name = "_".join(parts[1:-1]) if len(parts) > 3 else "*"
                else:
                    entity_type = "employee"
                    field = "salary"
                    entity_name = "*"
                
                monte_carlo.add_uncertainty(
                    entity_name, entity_type, field, distribution
                )
        else:
            # Use common uncertainties
            common_uncertainties = create_common_uncertainties()
            for uncertainty in common_uncertainties:
                monte_carlo.add_uncertainty(
                    uncertainty.entity_name,
                    uncertainty.entity_type,
                    uncertainty.field,
                    uncertainty.distribution
                )
        
        # For large simulations, run in background
        if request.iterations > 1000:
            job_id = str(uuid.uuid4())
            
            # Store job info
            analysis_jobs[job_id] = {
                "status": "queued",
                "progress": 0.0,
                "created_at": date.today().isoformat(),
                "updated_at": date.today().isoformat(),
                "type": "monte_carlo",
                "request": request,
                "result": None,
                "error_message": None
            }
            
            # Start background task
            background_tasks.add_task(
                _run_monte_carlo_background,
                job_id, monte_carlo, start_date, end_date, request
            )
            
            return MonteCarloResponse(
                scenario=request.scenario,
                iterations=request.iterations,
                start_date=start_date,
                end_date=end_date,
                metrics=[],
                success_probability=0.0,
                risk_metrics={},
                job_id=job_id
            )
        
        else:
            # Run simulation directly
            results = monte_carlo.run_simulation(
                start_date=start_date,
                end_date=end_date,
                num_simulations=request.iterations,
                confidence_levels=request.confidence_levels,
                parallel=True,
                max_workers=4
            )
            
            # Convert results to response format
            return _format_monte_carlo_response(
                results, request, start_date, end_date
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run Monte Carlo simulation: {str(e)}"
        )


@router.post("/sensitivity", response_model=SensitivityResponse)
async def run_sensitivity_analysis(
    request: SensitivityRequest,
    components: dict = Depends(get_analysis_components),
    current_user: dict = Depends(get_current_user)
):
    """
    Run sensitivity analysis for a specific variable.
    """
    try:
        # Setup dates
        start_date = request.start_date or date.today()
        end_date = start_date + timedelta(days=request.months * 30)
        
        whatif_analyzer = components["whatif_analyzer"]
        
        # Parse variable range
        var_range = request.variable_range
        min_val = var_range.get("min", 0.5)
        max_val = var_range.get("max", 2.0)
        step = var_range.get("step", 0.1)
        
        # Generate value range
        import numpy as np
        values = np.arange(min_val, max_val + step, step).tolist()
        
        # Find entities matching the variable
        entities = components["store"].query({})
        matching_entities = []
        
        for entity in entities:
            if hasattr(entity, request.variable):
                matching_entities.append(entity)
        
        if not matching_entities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No entities found with variable '{request.variable}'"
            )
        
        # Use first matching entity for analysis
        entity = matching_entities[0]
        base_value = getattr(entity, request.variable, 1.0)
        
        # Create parameter for analysis
        parameter = Parameter(
            name=f"{entity.name}_{request.variable}",
            entity_name=entity.name,
            entity_type=entity.type,
            field=request.variable,
            base_value=base_value
        )
        
        # Convert relative values to absolute values
        absolute_values = [base_value * v for v in values]
        
        # Run sensitivity analysis
        sensitivity_results = whatif_analyzer.run_sensitivity_analysis(
            parameter, absolute_values, start_date, end_date
        )
        
        # Extract data points
        data_points = []
        metrics = sensitivity_results["metrics"]
        
        for i, value in enumerate(values):
            if i < len(metrics[request.target_metric]):
                metric_value = metrics[request.target_metric][i]
                cash_balance = metrics["final_cash_balance"][i]
                
                point = SensitivityPoint(
                    variable_value=value,
                    metric_value=metric_value,
                    cash_balance=cash_balance
                )
                data_points.append(point)
        
        # Calculate elasticity
        elasticity = 0.0
        break_even_value = None
        
        if len(data_points) > 1:
            # Simple elasticity calculation
            first_point = data_points[0]
            last_point = data_points[-1]
            
            var_change = (last_point.variable_value - first_point.variable_value) / first_point.variable_value
            metric_change = (last_point.metric_value - first_point.metric_value) / abs(first_point.metric_value) if first_point.metric_value != 0 else 0
            
            if var_change != 0:
                elasticity = metric_change / var_change
            
            # Find break-even value (where target metric = 0)
            for point in data_points:
                if abs(point.metric_value) < abs(point.metric_value * 0.01):  # Within 1% of zero
                    break_even_value = point.variable_value
                    break
        
        return SensitivityResponse(
            scenario=request.scenario,
            variable=request.variable,
            target_metric=request.target_metric,
            start_date=start_date,
            end_date=end_date,
            data_points=data_points,
            elasticity=elasticity,
            break_even_value=break_even_value
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run sensitivity analysis: {str(e)}"
        )


@router.get("/results/{job_id}", response_model=AnalysisJobResponse)
async def get_analysis_results(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get results of a long-running analysis job.
    """
    if job_id not in analysis_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job '{job_id}' not found"
        )
    
    job_info = analysis_jobs[job_id]
    
    # Create job status
    job_status = AnalysisJobStatus(
        job_id=job_id,
        status=job_info["status"],
        progress=job_info["progress"],
        created_at=job_info["created_at"],
        updated_at=job_info["updated_at"],
        error_message=job_info.get("error_message"),
        result_available=job_info["result"] is not None
    )
    
    # Include result if completed
    result = None
    if job_info["status"] == "completed" and job_info["result"]:
        result = job_info["result"]
    
    return AnalysisJobResponse(
        job_status=job_status,
        result=result
    )


@router.delete("/results/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_analysis_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel or clean up an analysis job.
    """
    if job_id in analysis_jobs:
        del analysis_jobs[job_id]


# Background task functions

async def _run_monte_carlo_background(
    job_id: str,
    monte_carlo: MonteCarloSimulator,
    start_date: date,
    end_date: date,
    request: MonteCarloRequest
):
    """Run Monte Carlo simulation in background."""
    try:
        # Update job status
        analysis_jobs[job_id]["status"] = "running"
        analysis_jobs[job_id]["progress"] = 0.1
        analysis_jobs[job_id]["updated_at"] = date.today().isoformat()
        
        # Run simulation
        results = monte_carlo.run_simulation(
            start_date=start_date,
            end_date=end_date,
            num_simulations=request.iterations,
            confidence_levels=request.confidence_levels,
            parallel=True,
            max_workers=4
        )
        
        # Format response
        response = _format_monte_carlo_response(
            results, request, start_date, end_date
        )
        
        # Update job with results
        analysis_jobs[job_id]["status"] = "completed"
        analysis_jobs[job_id]["progress"] = 1.0
        analysis_jobs[job_id]["result"] = response
        analysis_jobs[job_id]["updated_at"] = date.today().isoformat()
        
    except Exception as e:
        # Update job with error
        analysis_jobs[job_id]["status"] = "failed"
        analysis_jobs[job_id]["error_message"] = str(e)
        analysis_jobs[job_id]["updated_at"] = date.today().isoformat()


# Helper functions

def _format_monte_carlo_response(
    results: Dict,
    request: MonteCarloRequest,
    start_date: date,
    end_date: date
) -> MonteCarloResponse:
    """Format Monte Carlo results into API response."""
    
    # Convert percentiles to metrics
    metrics = []
    percentiles = results.get("percentiles", {})
    
    for metric_name, metric_data in percentiles.items():
        if isinstance(metric_data, dict):
            percentile_dict = {
                f"p{int(cl*100)}": metric_data.get(f"p{int(cl*100)}", 0)
                for cl in request.confidence_levels
            }
            
            metric = MonteCarloMetrics(
                metric=metric_name,
                mean=metric_data.get("mean", 0),
                std=metric_data.get("std", 0),
                min=metric_data.get("min", 0),
                max=metric_data.get("max", 0),
                percentiles=percentile_dict
            )
            metrics.append(metric)
    
    # Extract success probability and risk metrics
    summary = results.get("summary", {})
    success_probability = summary.get("probability_positive_balance", 0.0)
    
    risk_metrics = results.get("risk_metrics", {})
    
    return MonteCarloResponse(
        scenario=request.scenario,
        iterations=results.get("num_simulations", request.iterations),
        start_date=start_date,
        end_date=end_date,
        metrics=metrics,
        success_probability=success_probability,
        risk_metrics=risk_metrics,
        job_id=None
    )