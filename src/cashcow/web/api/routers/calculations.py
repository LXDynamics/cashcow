"""
CashCow Web API - Calculations and KPI router.
Mock implementation for development.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

# Create router
router = APIRouter(prefix="/calculations", tags=["calculations"])

def get_current_user():
    """Mock user for development."""
    return {"user_id": "dev-user", "username": "developer"}

# Mock KPI data
MOCK_KPIS = [
    {
        "name": "Monthly Recurring Revenue",
        "value": 15000,
        "unit": "$",
        "change": 0.125,
        "change_period": "month",
        "trend": "up",
        "category": "revenue"
    },
    {
        "name": "Total Cash Available",
        "value": 2750000,
        "unit": "$",
        "change": -0.045,
        "change_period": "month",
        "trend": "down",
        "category": "cash_flow"
    },
    {
        "name": "Burn Rate",
        "value": 22250,
        "unit": "$/month",
        "change": -0.08,
        "change_period": "month",
        "trend": "down",
        "category": "expenses"
    },
    {
        "name": "Runway",
        "value": 18.5,
        "unit": "months",
        "change": 0.15,
        "change_period": "month",
        "trend": "up",
        "category": "cash_flow"
    },
    {
        "name": "Employee Count",
        "value": 8,
        "unit": "people",
        "change": 0.0,
        "change_period": "month",
        "trend": "stable",
        "category": "expenses"
    },
    {
        "name": "Revenue Growth Rate",
        "value": 0.125,
        "unit": "%",
        "change": 0.032,
        "change_period": "month",
        "trend": "up",
        "category": "revenue"
    }
]

# Mock forecast data
MOCK_FORECAST = {
    "months": [
        {
            "month": "2024-01",
            "revenue": 85000,
            "expenses": 125000,
            "net_cash_flow": -40000,
            "cumulative_cash_flow": -40000,
            "burn_rate": 40000
        },
        {
            "month": "2024-02", 
            "revenue": 92000,
            "expenses": 128000,
            "net_cash_flow": -36000,
            "cumulative_cash_flow": -76000,
            "burn_rate": 36000
        },
        {
            "month": "2024-03",
            "revenue": 165000,
            "expenses": 132000,
            "net_cash_flow": 33000,
            "cumulative_cash_flow": -43000,
            "burn_rate": 0
        },
        {
            "month": "2024-04",
            "revenue": 105000,
            "expenses": 135000,
            "net_cash_flow": -30000,
            "cumulative_cash_flow": -73000,
            "burn_rate": 30000
        },
        {
            "month": "2024-05",
            "revenue": 112000,
            "expenses": 138000,
            "net_cash_flow": -26000,
            "cumulative_cash_flow": -99000,
            "burn_rate": 26000
        },
        {
            "month": "2024-06",
            "revenue": 275000,
            "expenses": 142000,
            "net_cash_flow": 133000,
            "cumulative_cash_flow": 34000,
            "burn_rate": 0
        }
    ],
    "summary": {
        "total_revenue": 834000,
        "total_expenses": 800000,
        "net_cash_flow": 34000,
        "average_burn_rate": 22000,
        "runway_months": 18.5
    }
}

@router.get("/kpis")
async def get_kpis(
    current_user: dict = Depends(get_current_user)
):
    """
    Get Key Performance Indicators.
    """
    return {
        "success": True,
        "data": MOCK_KPIS
    }

@router.get("/forecast")
async def get_forecast(
    months: Optional[int] = Query(12, description="Number of months to forecast"),
    scenario: Optional[str] = Query("baseline", description="Scenario name"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate cash flow forecast.
    """
    # Simulate different scenarios
    forecast_data = MOCK_FORECAST.copy()
    
    if scenario == "optimistic":
        # Increase revenue by 20%
        for month in forecast_data["months"]:
            month["revenue"] = int(month["revenue"] * 1.2)
            month["net_cash_flow"] = month["revenue"] - month["expenses"]
            
    elif scenario == "conservative":
        # Decrease revenue by 15%
        for month in forecast_data["months"]:
            month["revenue"] = int(month["revenue"] * 0.85)
            month["net_cash_flow"] = month["revenue"] - month["expenses"]
    
    # Adjust number of months
    if months != 6:
        forecast_data["months"] = forecast_data["months"][:months]
    
    return {
        "success": True,
        "data": forecast_data
    }

@router.post("/recalculate")
async def recalculate_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger recalculation of all metrics.
    """
    # In a real implementation, this would trigger background calculation jobs
    return {
        "success": True,
        "message": "Recalculation started",
        "job_id": "calc_12345"
    }

@router.get("/status")
async def get_calculation_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get calculation status.
    """
    return {
        "success": True,
        "data": {
            "status": "completed",
            "last_calculation": "2024-07-20T12:30:00Z",
            "next_scheduled": "2024-07-20T18:00:00Z"
        }
    }