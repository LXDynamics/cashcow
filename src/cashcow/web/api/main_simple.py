"""
Simplified CashCow API for development
"""

from fastapi import FastAPI, Query
from typing import Optional
import uuid

app = FastAPI(title="CashCow API", version="0.1.0")

# Mock data
MOCK_ENTITIES = [
    {
        "id": "emp1",
        "type": "employee",
        "name": "John Smith",
        "start_date": "2024-01-01",
        "salary": 150000,
        "position": "CEO",
        "tags": ["executive", "founder"],
        "is_active": True,
        "extra_fields": {"department": "Executive"}
    },
    {
        "id": "emp2", 
        "type": "employee",
        "name": "Jane Doe",
        "start_date": "2024-02-01",
        "salary": 120000,
        "position": "Senior Engineer",
        "tags": ["engineering"],
        "is_active": True,
        "extra_fields": {"department": "Engineering"}
    },
    {
        "id": "grant1",
        "type": "grant",
        "name": "NSF SBIR Phase II",
        "start_date": "2024-01-01",
        "amount": 750000,
        "agency": "NSF",
        "tags": ["funding"],
        "is_active": True,
        "extra_fields": {"program": "SBIR"}
    }
]

MOCK_KPIS = [
    {
        "name": "Monthly Recurring Revenue",
        "value": 15000,
        "unit": "$",
        "change": 0.125,
        "trend": "up",
        "category": "revenue"
    },
    {
        "name": "Total Cash Available",
        "value": 2750000,
        "unit": "$",
        "change": -0.045,
        "trend": "down",
        "category": "cash_flow"
    },
    {
        "name": "Burn Rate",
        "value": 22250,
        "unit": "$/month",
        "change": -0.08,
        "trend": "down",
        "category": "expenses"
    }
]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cashcow-api", "version": "0.1.0"}

@app.get("/api/entities")
async def list_entities(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    type: Optional[str] = Query(None)
):
    entities = MOCK_ENTITIES.copy()
    
    # Apply type filter
    if type:
        entities = [e for e in entities if e["type"] == type]
    
    # Pagination
    total = len(entities)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_entities = entities[start_idx:end_idx]
    
    return {
        "success": True,
        "data": paginated_entities,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@app.get("/api/entities/{entity_id}")
async def get_entity(entity_id: str):
    entity = next((e for e in MOCK_ENTITIES if e["id"] == entity_id), None)
    if not entity:
        return {"success": False, "error": "Entity not found"}, 404
    
    return {"success": True, "data": entity}

@app.post("/api/entities")
async def create_entity(entity_data: dict):
    entity_id = str(uuid.uuid4())[:8]
    new_entity = {"id": entity_id, "is_active": True, **entity_data}
    MOCK_ENTITIES.append(new_entity)
    
    return {"success": True, "data": new_entity, "message": "Entity created"}

@app.get("/api/calculations/kpis")
async def get_kpis():
    return {"success": True, "data": MOCK_KPIS}

@app.get("/api/calculations/forecast")
async def get_forecast(months: int = Query(12)):
    forecast_data = {
        "months": [
            {
                "month": "2024-01",
                "revenue": 85000,
                "expenses": 125000,
                "net_cash_flow": -40000,
                "burn_rate": 40000
            },
            {
                "month": "2024-02", 
                "revenue": 92000,
                "expenses": 128000,
                "net_cash_flow": -36000,
                "burn_rate": 36000
            }
        ][:months],
        "summary": {
            "total_revenue": 177000,
            "total_expenses": 253000,
            "net_cash_flow": -76000,
            "runway_months": 18.5
        }
    }
    
    return {"success": True, "data": forecast_data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)