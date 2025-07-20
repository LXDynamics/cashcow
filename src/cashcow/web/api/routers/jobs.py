"""
Job management router for background tasks.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..tasks import job_manager
from ..tasks.background_jobs import (
    calculate_forecast_job,
    monte_carlo_simulation_job,
    entity_validation_job,
    report_generation_job
)
from ..models.websockets import JobRequest


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class ForecastJobRequest(BaseModel):
    """Request for forecast calculation job."""
    months: int = 12
    scenario: str = "baseline"


class MonteCarloJobRequest(BaseModel):
    """Request for Monte Carlo simulation job."""
    iterations: int = 1000
    variables: list[str] = ["revenue_growth", "expense_inflation"]


class ValidationJobRequest(BaseModel):
    """Request for entity validation job."""
    entities_dir: str = "entities"


class ReportJobRequest(BaseModel):
    """Request for report generation job."""
    report_type: str
    output_format: str = "html"


@router.post("/forecast")
async def start_forecast_job(request: ForecastJobRequest):
    """Start a forecast calculation job."""
    job_id = await job_manager.submit_job(
        job_func=calculate_forecast_job,
        job_kwargs={
            "months": request.months,
            "scenario": request.scenario
        },
        metadata={
            "job_type": "forecast",
            "months": request.months,
            "scenario": request.scenario
        }
    )
    
    return {
        "job_id": job_id,
        "status": "submitted",
        "message": f"Forecast job started for {request.months} months using {request.scenario} scenario"
    }


@router.post("/monte-carlo")
async def start_monte_carlo_job(request: MonteCarloJobRequest):
    """Start a Monte Carlo simulation job."""
    job_id = await job_manager.submit_job(
        job_func=monte_carlo_simulation_job,
        job_kwargs={
            "iterations": request.iterations,
            "variables": request.variables
        },
        metadata={
            "job_type": "monte_carlo",
            "iterations": request.iterations,
            "variables": request.variables
        }
    )
    
    return {
        "job_id": job_id,
        "status": "submitted",
        "message": f"Monte Carlo simulation started with {request.iterations} iterations"
    }


@router.post("/validate")
async def start_validation_job(request: ValidationJobRequest):
    """Start an entity validation job."""
    job_id = await job_manager.submit_job(
        job_func=entity_validation_job,
        job_kwargs={
            "entities_dir": request.entities_dir
        },
        metadata={
            "job_type": "validation",
            "entities_dir": request.entities_dir
        }
    )
    
    return {
        "job_id": job_id,
        "status": "submitted",
        "message": f"Entity validation job started for {request.entities_dir}"
    }


@router.post("/report")
async def start_report_job(request: ReportJobRequest):
    """Start a report generation job."""
    job_id = await job_manager.submit_job(
        job_func=report_generation_job,
        job_kwargs={
            "report_type": request.report_type,
            "output_format": request.output_format
        },
        metadata={
            "job_type": "report",
            "report_type": request.report_type,
            "output_format": request.output_format
        }
    )
    
    return {
        "job_id": job_id,
        "status": "submitted",
        "message": f"Report generation job started: {request.report_type} ({request.output_format})"
    }