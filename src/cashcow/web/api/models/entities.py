"""
CashCow Web API - Entity models for API requests and responses.
"""

from datetime import date
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

# Import existing entity models
from cashcow.models.base import BaseEntity
from cashcow.models.employee import Employee
from cashcow.models.revenue import Grant, Investment, Sale, Service
from cashcow.models.expense import Facility, Software, Equipment
from cashcow.models.project import Project


class EntityCreateRequest(BaseModel):
    """Request model for creating a new entity."""
    model_config = ConfigDict(extra='allow')
    
    type: str = Field(..., description="Entity type (employee, grant, project, etc.)")
    name: str = Field(..., description="Entity name")
    start_date: date = Field(..., description="Entity start date")
    end_date: Optional[date] = Field(None, description="Entity end date")
    tags: List[str] = Field(default_factory=list, description="Entity tags")
    notes: Optional[str] = Field(None, description="Additional notes")


class EntityUpdateRequest(BaseModel):
    """Request model for updating an entity."""
    model_config = ConfigDict(extra='allow')
    
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class EntityResponse(BaseModel):
    """Response model for entity data."""
    model_config = ConfigDict(extra='allow', from_attributes=True)
    
    id: str = Field(..., description="Unique entity identifier")
    type: str = Field(..., description="Entity type")
    name: str = Field(..., description="Entity name")
    start_date: date = Field(..., description="Entity start date")
    end_date: Optional[date] = Field(None, description="Entity end date")
    tags: List[str] = Field(default_factory=list, description="Entity tags")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_active: bool = Field(..., description="Whether entity is currently active")
    extra_fields: Dict[str, Any] = Field(default_factory=dict, description="Additional entity-specific fields")


class EntityListResponse(BaseModel):
    """Response model for entity list with pagination."""
    entities: List[EntityResponse]
    total: int = Field(..., description="Total number of entities")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(50, description="Number of items per page")
    has_next: bool = Field(False, description="Whether there are more pages")


class EntitySummary(BaseModel):
    """Simplified entity summary for lists and quick views."""
    id: str
    type: str
    name: str
    start_date: date
    end_date: Optional[date]
    is_active: bool
    status: str = Field(..., description="Entity status (active, inactive, future)")


class EntityValidationResponse(BaseModel):
    """Response model for entity validation results."""
    valid: bool = Field(..., description="Whether entity is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class EntityTypeInfo(BaseModel):
    """Information about available entity types."""
    type: str = Field(..., description="Entity type identifier")
    display_name: str = Field(..., description="Human-readable type name")
    description: str = Field(..., description="Type description")
    required_fields: List[str] = Field(..., description="Required fields for this type")
    optional_fields: List[str] = Field(..., description="Common optional fields")
    example: Dict[str, Any] = Field(..., description="Example entity data")


class EntityTypesResponse(BaseModel):
    """Response model listing all available entity types."""
    types: List[EntityTypeInfo]


class BulkEntityOperation(BaseModel):
    """Request model for bulk entity operations."""
    entity_ids: List[str] = Field(..., description="List of entity IDs to operate on")
    operation: str = Field(..., description="Operation to perform (delete, update, tag)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""
    success_count: int = Field(..., description="Number of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="List of errors with entity IDs")
    warnings: List[Dict[str, str]] = Field(default_factory=list, description="List of warnings")


class EntitySearchRequest(BaseModel):
    """Request model for entity search."""
    query: Optional[str] = Field(None, description="Search query string")
    entity_types: Optional[List[str]] = Field(None, description="Filter by entity types")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    start_date_from: Optional[date] = Field(None, description="Filter entities starting after this date")
    start_date_to: Optional[date] = Field(None, description="Filter entities starting before this date")
    active_only: bool = Field(False, description="Only return active entities")
    inactive_only: bool = Field(False, description="Only return inactive entities")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=200, description="Items per page")
    sort_by: str = Field("name", description="Field to sort by")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


# Entity-specific request models for type-safe creation
class EmployeeCreateRequest(EntityCreateRequest):
    """Request model for creating an employee."""
    type: Literal["employee"] = "employee"
    salary: float = Field(..., gt=0, description="Annual salary")
    position: Optional[str] = None
    department: Optional[str] = None
    overhead_multiplier: float = Field(1.3, ge=1.0, le=3.0)


class GrantCreateRequest(EntityCreateRequest):
    """Request model for creating a grant."""
    type: Literal["grant"] = "grant"
    amount: float = Field(..., gt=0, description="Grant amount")
    agency: Optional[str] = None
    program: Optional[str] = None


class ProjectCreateRequest(EntityCreateRequest):
    """Request model for creating a project."""
    type: Literal["project"] = "project"
    total_budget: float = Field(..., gt=0, description="Total project budget")
    status: str = Field("planned", description="Project status")


# Union type for all entity creation requests
EntityCreateRequestUnion = Union[
    EmployeeCreateRequest,
    GrantCreateRequest,
    ProjectCreateRequest,
    EntityCreateRequest  # Fallback for other entity types
]