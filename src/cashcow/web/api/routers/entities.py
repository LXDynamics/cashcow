"""
CashCow Web API - Entity management router with CRUD operations.
"""

import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

# Import CashCow modules
from cashcow.models import create_entity, ENTITY_TYPES, BaseEntity
from cashcow.storage.yaml_loader import YamlEntityLoader
from cashcow.validation import validate_entity

# Import API models
from ..models.entities import (
    EntityCreateRequest,
    EntityUpdateRequest,
    EntityResponse,
    EntityListResponse,
    EntitySummary,
    EntityValidationResponse,
    EntityTypesResponse,
    EntityTypeInfo,
    EntitySearchRequest,
    BulkEntityOperation,
    BulkOperationResponse,
    EntityCreateRequestUnion
)
from ..dependencies import get_entity_loader, get_current_user
from ..exceptions import EntityNotFoundError, EntityValidationError

# Create router
router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/", response_model=EntityListResponse)
async def list_entities(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    active_only: bool = Query(False, description="Only return active entities"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    loader: YamlEntityLoader = Depends(get_entity_loader),
    current_user: dict = Depends(get_current_user)
):
    """
    List all entities with pagination and filtering.
    """
    try:
        # Load entities based on type filter
        if entity_type:
            entities = loader.load_by_type(entity_type)
        else:
            entities = loader.load_all()
        
        # Apply filters
        filtered_entities = []
        current_date = date.today()
        
        for entity in entities:
            # Active filter
            if active_only and not entity.is_active(current_date):
                continue
                
            # Tag filter
            if tag and tag not in entity.tags:
                continue
                
            filtered_entities.append(entity)
        
        # Calculate pagination
        total = len(filtered_entities)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_entities = filtered_entities[start_idx:end_idx]
        
        # Convert to response format
        entity_responses = []
        for entity in paginated_entities:
            # Generate unique ID from file path or name+type
            entity_id = _generate_entity_id(entity)
            
            # Extract extra fields (non-standard BaseEntity fields)
            extra_fields = {}
            entity_dict = entity.to_dict()
            base_fields = {'type', 'name', 'start_date', 'end_date', 'tags', 'notes', '_file_path'}
            
            for key, value in entity_dict.items():
                if key not in base_fields:
                    extra_fields[key] = value
            
            entity_response = EntityResponse(
                id=entity_id,
                type=entity.type,
                name=entity.name,
                start_date=entity.start_date,
                end_date=entity.end_date,
                tags=entity.tags or [],
                notes=entity.notes,
                is_active=entity.is_active(current_date),
                extra_fields=extra_fields
            )
            entity_responses.append(entity_response)
        
        return EntityListResponse(
            entities=entity_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end_idx < total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load entities: {str(e)}"
        )


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    loader: YamlEntityLoader = Depends(get_entity_loader),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific entity by ID.
    """
    entity = _find_entity_by_id(entity_id, loader)
    if not entity:
        raise EntityNotFoundError(entity_id)
    
    # Convert to response format
    current_date = date.today()
    entity_dict = entity.to_dict()
    
    # Extract extra fields
    extra_fields = {}
    base_fields = {'type', 'name', 'start_date', 'end_date', 'tags', 'notes', '_file_path'}
    
    for key, value in entity_dict.items():
        if key not in base_fields:
            extra_fields[key] = value
    
    return EntityResponse(
        id=entity_id,
        type=entity.type,
        name=entity.name,
        start_date=entity.start_date,
        end_date=entity.end_date,
        tags=entity.tags or [],
        notes=entity.notes,
        is_active=entity.is_active(current_date),
        extra_fields=extra_fields
    )


@router.post("/", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity_endpoint(
    entity_data: EntityCreateRequest,
    loader: YamlEntityLoader = Depends(get_entity_loader),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new entity.
    """
    try:
        # Convert request to dictionary
        entity_dict = entity_data.model_dump(exclude_unset=True)
        
        # Create entity object
        entity = create_entity(entity_dict)
        
        # Validate entity
        validation_result = validate_entity(entity)
        if not validation_result.is_valid:
            raise EntityValidationError("; ".join(validation_result.errors))
        
        # Save entity to file
        file_path = loader.save_entity(entity)
        
        # Generate entity ID
        entity_id = _generate_entity_id(entity)
        
        # Return response
        current_date = date.today()
        entity_dict = entity.to_dict()
        
        # Extract extra fields
        extra_fields = {}
        base_fields = {'type', 'name', 'start_date', 'end_date', 'tags', 'notes', '_file_path'}
        
        for key, value in entity_dict.items():
            if key not in base_fields:
                extra_fields[key] = value
        
        return EntityResponse(
            id=entity_id,
            type=entity.type,
            name=entity.name,
            start_date=entity.start_date,
            end_date=entity.end_date,
            tags=entity.tags or [],
            notes=entity.notes,
            is_active=entity.is_active(current_date),
            extra_fields=extra_fields
        )
        
    except EntityValidationError:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create entity: {str(e)}"
        )


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: str,
    update_data: EntityUpdateRequest,
    loader: YamlEntityLoader = Depends(get_entity_loader),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing entity.
    """
    # Find existing entity
    entity = _find_entity_by_id(entity_id, loader)
    if not entity:
        raise EntityNotFoundError(entity_id)
    
    try:
        # Get current entity data
        entity_dict = entity.to_dict()
        
        # Apply updates (only for provided fields)
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            entity_dict[key] = value
        
        # Create updated entity
        updated_entity = create_entity(entity_dict)
        
        # Validate updated entity
        validation_result = validate_entity(updated_entity)
        if not validation_result.is_valid:
            raise EntityValidationError("; ".join(validation_result.errors))
        
        # Save updated entity (overwrite existing file)
        file_path = entity_dict.get('_file_path')
        if file_path:
            loader.save_entity(updated_entity, file_path)
        else:
            loader.save_entity(updated_entity)
        
        # Return updated entity response
        current_date = date.today()
        updated_dict = updated_entity.to_dict()
        
        # Extract extra fields
        extra_fields = {}
        base_fields = {'type', 'name', 'start_date', 'end_date', 'tags', 'notes', '_file_path'}
        
        for key, value in updated_dict.items():
            if key not in base_fields:
                extra_fields[key] = value
        
        return EntityResponse(
            id=entity_id,
            type=updated_entity.type,
            name=updated_entity.name,
            start_date=updated_entity.start_date,
            end_date=updated_entity.end_date,
            tags=updated_entity.tags or [],
            notes=updated_entity.notes,
            is_active=updated_entity.is_active(current_date),
            extra_fields=extra_fields
        )
        
    except EntityValidationError:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update entity: {str(e)}"
        )


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: str,
    loader: YamlEntityLoader = Depends(get_entity_loader),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an entity.
    """
    # Find existing entity
    entity = _find_entity_by_id(entity_id, loader)
    if not entity:
        raise EntityNotFoundError(entity_id)
    
    try:
        # Get file path and delete file
        entity_dict = entity.to_dict()
        file_path = entity_dict.get('_file_path')
        
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entity file not found"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete entity: {str(e)}"
        )


@router.get("/types/available", response_model=EntityTypesResponse)
async def get_entity_types(
    current_user: dict = Depends(get_current_user)
):
    """
    Get information about available entity types.
    """
    type_info = []
    
    for entity_type, entity_class in ENTITY_TYPES.items():
        # Get model fields for documentation
        model_fields = entity_class.model_fields
        required_fields = []
        optional_fields = []
        
        for field_name, field_info in model_fields.items():
            if field_info.is_required():
                required_fields.append(field_name)
            else:
                optional_fields.append(field_name)
        
        # Create example entity data
        example = {
            "type": entity_type,
            "name": f"Example {entity_type.title()}",
            "start_date": "2024-01-01"
        }
        
        # Add type-specific example fields
        if entity_type == "employee":
            example["salary"] = 75000
            example["position"] = "Software Engineer"
        elif entity_type == "grant":
            example["amount"] = 100000
            example["agency"] = "NASA"
        elif entity_type == "project":
            example["total_budget"] = 50000
            example["status"] = "planned"
        
        type_info.append(EntityTypeInfo(
            type=entity_type,
            display_name=entity_type.replace('_', ' ').title(),
            description=f"{entity_type.title()} entity for CashCow financial modeling",
            required_fields=required_fields,
            optional_fields=optional_fields,
            example=example
        ))
    
    return EntityTypesResponse(types=type_info)


@router.post("/validate", response_model=EntityValidationResponse)
async def validate_entity_data(
    entity_data: EntityCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Validate entity data without creating the entity.
    """
    try:
        # Convert request to dictionary
        entity_dict = entity_data.model_dump(exclude_unset=True)
        
        # Create entity object for validation
        entity = create_entity(entity_dict)
        
        # Validate entity
        validation_result = validate_entity(entity)
        
        return EntityValidationResponse(
            valid=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings
        )
        
    except Exception as e:
        return EntityValidationResponse(
            valid=False,
            errors=[str(e)],
            warnings=[]
        )


# Helper functions

def _generate_entity_id(entity: BaseEntity) -> str:
    """
    Generate a unique ID for an entity.
    """
    # Use file path if available
    entity_dict = entity.to_dict()
    file_path = entity_dict.get('_file_path')
    
    if file_path:
        # Use file path hash for consistency
        return str(hash(file_path))[:16]
    
    # Fallback to name + type hash
    identifier = f"{entity.type}:{entity.name}:{entity.start_date}"
    return str(hash(identifier))[:16]


def _find_entity_by_id(entity_id: str, loader: YamlEntityLoader) -> Optional[BaseEntity]:
    """
    Find an entity by its generated ID.
    """
    # Load all entities and find matching ID
    entities = loader.load_all()
    
    for entity in entities:
        if _generate_entity_id(entity) == entity_id:
            return entity
    
    return None