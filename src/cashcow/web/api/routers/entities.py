"""
CashCow Web API - Entity management router with CRUD operations.
Mock implementation for development.
"""

import uuid
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
import yaml

# Create router
router = APIRouter(prefix="/entities", tags=["entities"])

# Mock entity data for development
MOCK_ENTITIES = [
    {
        "id": "emp1",
        "type": "employee",
        "name": "John Smith",
        "start_date": "2024-01-01",
        "end_date": None,
        "salary": 150000,
        "position": "CEO",
        "tags": ["executive", "founder"],
        "notes": "Company founder and CEO",
        "is_active": True,
        "extra_fields": {
            "overhead_multiplier": 1.4,
            "equity_eligible": True,
            "department": "Executive"
        }
    },
    {
        "id": "emp2", 
        "type": "employee",
        "name": "Jane Doe",
        "start_date": "2024-02-01",
        "end_date": None,
        "salary": 120000,
        "position": "Senior Engineer",
        "tags": ["engineering"],
        "notes": "Lead developer for core platform",
        "is_active": True,
        "extra_fields": {
            "overhead_multiplier": 1.3,
            "equity_eligible": True,
            "department": "Engineering"
        }
    },
    {
        "id": "grant1",
        "type": "grant",
        "name": "NSF SBIR Phase II",
        "start_date": "2024-01-01",
        "end_date": "2025-12-31",
        "amount": 750000,
        "agency": "NSF",
        "tags": ["funding", "research"],
        "notes": "Phase II continuation of successful Phase I project",
        "is_active": True,
        "extra_fields": {
            "program": "SBIR",
            "indirect_cost_rate": 0.25,
            "grant_number": "IIP-2345678"
        }
    },
    {
        "id": "facility1",
        "type": "facility", 
        "name": "Main Office",
        "start_date": "2024-01-01",
        "end_date": None,
        "monthly_cost": 8000,
        "location": "Tech City, CA",
        "tags": ["office"],
        "notes": "Primary office location with conference rooms and lab space",
        "is_active": True,
        "extra_fields": {
            "size_sqft": 5000,
            "facility_type": "office",
            "utilities_monthly": 1200
        }
    },
    {
        "id": "project1",
        "type": "project",
        "name": "Advanced Rocket Engine Development", 
        "start_date": "2024-01-01",
        "end_date": "2025-12-31",
        "total_budget": 1000000,
        "status": "active",
        "tags": ["development", "research"],
        "notes": "Next-generation rocket engine for small satellite launches",
        "is_active": True,
        "extra_fields": {
            "completion_percentage": 25,
            "priority": "high",
            "project_manager": "John Smith"
        }
    }
]

def get_current_user():
    """Mock user for development."""
    return {"user_id": "dev-user", "username": "developer"}

@router.get("/")
async def list_entities(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),  
    type: Optional[str] = Query(None, description="Filter by entity type"),
    active_only: bool = Query(False, description="Only return active entities"),
    search: Optional[str] = Query(None, description="Search in entity names"),
    current_user: dict = Depends(get_current_user)
):
    """
    List all entities with pagination and filtering.
    """
    try:
        # Start with all entities
        entities = MOCK_ENTITIES.copy()
        
        # Apply filters
        if type:
            entities = [e for e in entities if e["type"] == type]
            
        if active_only:
            entities = [e for e in entities if e["is_active"]]
            
        if search:
            search_lower = search.lower()
            entities = [e for e in entities if search_lower in e["name"].lower()]
        
        # Calculate pagination
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
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load entities: {str(e)}"
        )


@router.get("/{entity_id}")
async def get_entity(
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific entity by ID.
    """
    entity = next((e for e in MOCK_ENTITIES if e["id"] == entity_id), None)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with ID {entity_id} not found"
        )
    
    return {
        "success": True,
        "data": entity
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new entity.
    """
    try:
        # Generate new ID
        entity_id = str(uuid.uuid4())[:8]
        
        # Create new entity
        new_entity = {
            "id": entity_id,
            "is_active": True,
            **entity_data
        }
        
        # Add to mock data (in a real implementation, this would save to database)
        MOCK_ENTITIES.append(new_entity)
        
        return {
            "success": True,
            "data": new_entity,
            "message": "Entity created successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create entity: {str(e)}"
        )


@router.put("/{entity_id}")
async def update_entity(
    entity_id: str,
    update_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing entity.
    """
    # Find entity
    entity_index = next((i for i, e in enumerate(MOCK_ENTITIES) if e["id"] == entity_id), None)
    if entity_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with ID {entity_id} not found"
        )
    
    try:
        # Update entity
        MOCK_ENTITIES[entity_index].update(update_data)
        
        return {
            "success": True,
            "data": MOCK_ENTITIES[entity_index],
            "message": "Entity updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update entity: {str(e)}"
        )


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an entity.
    """
    # Find entity
    entity_index = next((i for i, e in enumerate(MOCK_ENTITIES) if e["id"] == entity_id), None)
    if entity_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with ID {entity_id} not found"
        )
    
    try:
        # Remove entity
        MOCK_ENTITIES.pop(entity_index)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete entity: {str(e)}"
        )


@router.get("/types/available")
async def get_entity_types(
    current_user: dict = Depends(get_current_user)
):
    """
    Get information about available entity types.
    """
    entity_types = [
        {
            "type": "employee",
            "display_name": "Employee",
            "description": "Company employees and contractors",
            "required_fields": ["name", "start_date", "salary"],
            "optional_fields": ["position", "department", "equity_eligible"],
            "example": {
                "type": "employee",
                "name": "John Doe",
                "start_date": "2024-01-01", 
                "salary": 75000,
                "position": "Software Engineer"
            }
        },
        {
            "type": "grant",
            "display_name": "Grant",
            "description": "Government and institutional grants",
            "required_fields": ["name", "start_date", "amount"],
            "optional_fields": ["agency", "program", "indirect_cost_rate"],
            "example": {
                "type": "grant",
                "name": "SBIR Phase I",
                "start_date": "2024-01-01",
                "amount": 100000,
                "agency": "NASA"
            }
        },
        {
            "type": "project",
            "display_name": "Project", 
            "description": "Development projects and initiatives",
            "required_fields": ["name", "start_date", "total_budget"],
            "optional_fields": ["status", "priority", "completion_percentage"],
            "example": {
                "type": "project",
                "name": "New Product Development",
                "start_date": "2024-01-01",
                "total_budget": 50000,
                "status": "planned"
            }
        },
        {
            "type": "facility",
            "display_name": "Facility",
            "description": "Office spaces and facilities",
            "required_fields": ["name", "start_date", "monthly_cost"],
            "optional_fields": ["location", "size_sqft", "facility_type"],
            "example": {
                "type": "facility",
                "name": "Main Office",
                "start_date": "2024-01-01",
                "monthly_cost": 5000,
                "location": "San Francisco, CA"
            }
        }
    ]
    
    return {
        "success": True,
        "data": entity_types
    }