"""
CashCow Web API - File handling endpoints.
"""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from cashcow.storage.database import EntityStore
from ..dependencies import get_store
from ..models.reports import (
    FileUploadRequest, FileUploadResponse, FileValidationResult,
    FileExportRequest, FileExportResponse, FileTemplateListResponse,
    FileTemplateInfo
)
from ..files import FileProcessor, FileValidator, FileExporter

router = APIRouter(prefix="/files", tags=["files"])

# Global instances (in production, these would be properly injected)
_file_processor: Optional[FileProcessor] = None
_file_validator: Optional[FileValidator] = None
_file_exporter: Optional[FileExporter] = None


def get_file_processor(store: EntityStore = Depends(get_store)) -> FileProcessor:
    """Get file processor instance."""
    global _file_processor
    if _file_processor is None:
        _file_processor = FileProcessor(store)
    return _file_processor


def get_file_validator() -> FileValidator:
    """Get file validator instance."""
    global _file_validator
    if _file_validator is None:
        _file_validator = FileValidator()
    return _file_validator


def get_file_exporter(store: EntityStore = Depends(get_store)) -> FileExporter:
    """Get file exporter instance."""
    global _file_exporter
    if _file_exporter is None:
        _file_exporter = FileExporter(store)
    return _file_exporter


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    file_type: str = Form(..., description="File type (yaml, csv, excel)"),
    entity_type: Optional[str] = Form(None, description="Target entity type"),
    validate_only: bool = Form(False, description="Only validate, don't save"),
    overwrite_existing: bool = Form(False, description="Overwrite existing entities"),
    processor: FileProcessor = Depends(get_file_processor)
):
    """Upload and process entity file."""
    # Validate file size (limit to 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    # Validate file type
    allowed_types = ["yaml", "csv", "excel", "xlsx"]
    if file_type.lower() not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {allowed_types}"
        )
    
    # Create upload request
    upload_request = FileUploadRequest(
        file_type=file_type,
        entity_type=entity_type,
        validate_only=validate_only,
        overwrite_existing=overwrite_existing
    )
    
    try:
        response = await processor.process_upload(file, upload_request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File processing failed: {str(e)}"
        )


@router.post("/validate", response_model=FileValidationResult)
async def validate_file(
    file: UploadFile = File(..., description="File to validate"),
    file_type: str = Form(..., description="File type (yaml, csv, excel)"),
    entity_type: Optional[str] = Form(None, description="Expected entity type"),
    processor: FileProcessor = Depends(get_file_processor)
):
    """Validate file without saving entities."""
    # Validate file size
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    try:
        result = await processor.validate_file_only(file, file_type, entity_type)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File validation failed: {str(e)}"
        )


@router.get("/uploads", response_model=List[FileUploadResponse])
async def list_uploads(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    processor: FileProcessor = Depends(get_file_processor)
):
    """List file uploads with pagination."""
    result = processor.list_uploads(page, page_size)
    
    uploads = result["uploads"]
    
    # Apply status filter if provided
    if status_filter:
        uploads = [u for u in uploads if u.status == status_filter]
    
    return uploads


@router.get("/uploads/{upload_id}", response_model=FileUploadResponse)
async def get_upload(
    upload_id: str,
    processor: FileProcessor = Depends(get_file_processor)
):
    """Get specific upload by ID."""
    upload = processor.get_upload(upload_id)
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload not found: {upload_id}"
        )
    return upload


@router.post("/export", response_model=FileExportResponse)
async def export_entities(
    request: FileExportRequest,
    exporter: FileExporter = Depends(get_file_exporter)
):
    """Export entities to file."""
    # Validate export format
    allowed_formats = ["yaml", "csv", "excel", "json"]
    if request.format.lower() not in allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format. Allowed: {allowed_formats}"
        )
    
    try:
        response = await exporter.export_entities(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/exports", response_model=List[FileExportResponse])
async def list_exports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    format_filter: Optional[str] = Query(None, description="Filter by format"),
    exporter: FileExporter = Depends(get_file_exporter)
):
    """List file exports with pagination."""
    result = exporter.list_exports(page, page_size)
    
    exports = result["exports"]
    
    # Apply format filter if provided
    if format_filter:
        exports = [e for e in exports if e.format == format_filter]
    
    return exports


@router.get("/exports/{export_id}", response_model=FileExportResponse)
async def get_export(
    export_id: str,
    exporter: FileExporter = Depends(get_file_exporter)
):
    """Get specific export by ID."""
    export = exporter.get_export(export_id)
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export not found: {export_id}"
        )
    return export


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: str,
    exporter: FileExporter = Depends(get_file_exporter)
):
    """Download exported file."""
    export = exporter.get_export(export_id)
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export not found: {export_id}"
        )
    
    file_path = Path(export.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    
    # Determine media type based on format
    media_type_map = {
        "yaml": "application/x-yaml",
        "csv": "text/csv",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json"
    }
    
    media_type = media_type_map.get(export.format, "application/octet-stream")
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=export.file_name,
        headers={"Content-Disposition": f"attachment; filename={export.file_name}"}
    )


@router.get("/templates", response_model=FileTemplateListResponse)
async def list_file_templates(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    format: Optional[str] = Query(None, description="Filter by format"),
    exporter: FileExporter = Depends(get_file_exporter)
):
    """List available file templates."""
    templates = exporter.get_available_templates()
    
    # Apply filters
    if entity_type:
        templates = [t for t in templates if t.entity_type == entity_type]
    
    if format:
        templates = [t for t in templates if t.format == format]
    
    return FileTemplateListResponse(templates=templates)


@router.get("/templates/{entity_type}/{format}")
async def download_template(
    entity_type: str,
    format: str,
    include_sample: bool = Query(True, description="Include sample data"),
    exporter: FileExporter = Depends(get_file_exporter),
    validator: FileValidator = Depends(get_file_validator)
):
    """Download template file for entity type."""
    # Validate entity type
    supported_types = validator.get_supported_entity_types()
    if entity_type not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported entity type. Supported: {supported_types}"
        )
    
    # Validate format
    allowed_formats = ["yaml", "csv", "excel", "json"]
    if format.lower() not in allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format. Allowed: {allowed_formats}"
        )
    
    try:
        template_path = await exporter.generate_template_file(
            entity_type, format, include_sample
        )
        
        # Determine media type
        media_type_map = {
            "yaml": "application/x-yaml",
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "json": "application/json"
        }
        
        media_type = media_type_map.get(format.lower(), "application/octet-stream")
        filename = f"{entity_type}_template.{format}"
        
        return FileResponse(
            path=str(template_path),
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template generation failed: {str(e)}"
        )


@router.get("/entity-types")
async def list_entity_types(
    validator: FileValidator = Depends(get_file_validator)
):
    """List supported entity types."""
    entity_types = validator.get_supported_entity_types()
    
    # Get field information for each type
    type_info = {}
    for entity_type in entity_types:
        type_info[entity_type] = validator.get_entity_field_info(entity_type)
    
    return {
        "entity_types": entity_types,
        "type_info": type_info
    }


@router.get("/entity-types/{entity_type}/schema")
async def get_entity_type_schema(
    entity_type: str,
    validator: FileValidator = Depends(get_file_validator)
):
    """Get schema information for entity type."""
    supported_types = validator.get_supported_entity_types()
    if entity_type not in supported_types:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity type not found: {entity_type}"
        )
    
    field_info = validator.get_entity_field_info(entity_type)
    template = validator.get_entity_template(entity_type)
    
    return {
        "entity_type": entity_type,
        "field_info": field_info,
        "template": template
    }


@router.post("/cleanup")
async def cleanup_old_files(
    max_age_days: int = Query(7, ge=1, le=365, description="Maximum age in days"),
    processor: FileProcessor = Depends(get_file_processor),
    exporter: FileExporter = Depends(get_file_exporter)
):
    """Clean up old upload and export files."""
    processor.cleanup_old_uploads(max_age_days)
    exporter.cleanup_old_exports(max_age_days)
    
    return {"message": f"Cleaned up files older than {max_age_days} days"}


@router.get("/statistics/uploads")
async def get_upload_statistics(
    processor: FileProcessor = Depends(get_file_processor)
):
    """Get file upload statistics."""
    return processor.get_upload_statistics()


@router.get("/statistics/exports")
async def get_export_statistics(
    exporter: FileExporter = Depends(get_file_exporter)
):
    """Get file export statistics."""
    return exporter.get_export_statistics()


@router.post("/bulk-validate")
async def bulk_validate_entities(
    entities: List[dict],
    entity_type: Optional[str] = None,
    validator: FileValidator = Depends(get_file_validator)
):
    """Validate multiple entities in bulk."""
    results = []
    
    for i, entity_data in enumerate(entities):
        # Add entity type if specified and not present
        if entity_type and 'type' not in entity_data:
            entity_data['type'] = entity_type
        
        # Validate entity
        errors = validator.validate_entity_data(entity_data)
        
        results.append({
            "index": i,
            "entity_name": entity_data.get("name", f"Entity {i+1}"),
            "valid": len(errors) == 0,
            "errors": errors
        })
    
    # Summary statistics
    total_entities = len(entities)
    valid_entities = len([r for r in results if r["valid"]])
    
    return {
        "validation_results": results,
        "summary": {
            "total_entities": total_entities,
            "valid_entities": valid_entities,
            "invalid_entities": total_entities - valid_entities,
            "validation_rate": (valid_entities / max(total_entities, 1)) * 100
        }
    }


# Batch operations
@router.post("/batch-export")
async def batch_export_by_types(
    entity_types: List[str],
    format: str = "yaml",
    include_metadata: bool = True,
    exporter: FileExporter = Depends(get_file_exporter)
):
    """Export multiple entity types in separate files."""
    exports = []
    
    for entity_type in entity_types:
        try:
            request = FileExportRequest(
                format=format,
                entity_types=[entity_type],
                include_metadata=include_metadata
            )
            
            export_response = await exporter.export_entities(request)
            exports.append({
                "entity_type": entity_type,
                "export_id": export_response.export_id,
                "file_name": export_response.file_name,
                "entity_count": export_response.entity_count,
                "status": "success"
            })
            
        except Exception as e:
            exports.append({
                "entity_type": entity_type,
                "error": str(e),
                "status": "failed"
            })
    
    return {
        "batch_exports": exports,
        "total_types": len(entity_types),
        "successful_exports": len([e for e in exports if e["status"] == "success"]),
        "failed_exports": len([e for e in exports if e["status"] == "failed"])
    }