"""
CashCow Web API - File upload and processing.
"""

import csv
import io
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yaml
from fastapi import UploadFile

from cashcow.models.base import BaseEntity
from cashcow.storage.database import EntityStore
from ..models.reports import (
    FileUploadRequest, FileUploadResponse, FileValidationResult
)
from .validators import FileValidator


class FileProcessor:
    """Handles file upload, validation, and entity creation."""
    
    def __init__(self, store: EntityStore, upload_dir: str = None):
        """Initialize file processor.
        
        Args:
            store: Entity store instance
            upload_dir: Directory for temporary file storage
        """
        self.store = store
        
        if upload_dir is None:
            self.upload_dir = Path(tempfile.gettempdir()) / "cashcow_uploads"
        else:
            self.upload_dir = Path(upload_dir)
        
        self.upload_dir.mkdir(exist_ok=True)
        
        self.validator = FileValidator()
        self._uploads: Dict[str, FileUploadResponse] = {}
    
    async def process_upload(self, file: UploadFile, request: FileUploadRequest) -> FileUploadResponse:
        """Process uploaded file.
        
        Args:
            file: Uploaded file
            request: Upload request parameters
            
        Returns:
            Upload response with validation results
        """
        upload_id = str(uuid.uuid4())
        
        try:
            # Save uploaded file temporarily
            file_path = await self._save_uploaded_file(file, upload_id)
            
            # Parse file content
            entities_data = await self._parse_file(file_path, request.file_type)
            
            # Validate entities
            validation_result = await self._validate_entities(
                entities_data, request.entity_type
            )
            
            created_entities = []
            if not request.validate_only and validation_result.is_valid:
                # Create entities if validation passed and not validate-only
                created_entities = await self._create_entities(
                    entities_data, request.overwrite_existing
                )
            
            # Create response
            response = FileUploadResponse(
                upload_id=upload_id,
                file_name=file.filename or "unknown",
                file_size=file.size or 0,
                status="completed" if validation_result.is_valid else "validation_failed",
                validation_result=validation_result,
                created_entities=created_entities,
                created_at=datetime.now()
            )
            
            self._uploads[upload_id] = response
            
            # Clean up temporary file
            file_path.unlink(missing_ok=True)
            
            return response
            
        except Exception as e:
            # Handle processing error
            error_response = FileUploadResponse(
                upload_id=upload_id,
                file_name=file.filename or "unknown",
                file_size=file.size or 0,
                status="error",
                validation_result=None,
                created_entities=[],
                error_message=str(e),
                created_at=datetime.now()
            )
            
            self._uploads[upload_id] = error_response
            return error_response
    
    async def _save_uploaded_file(self, file: UploadFile, upload_id: str) -> Path:
        """Save uploaded file to temporary location.
        
        Args:
            file: Uploaded file
            upload_id: Upload identifier
            
        Returns:
            Path to saved file
        """
        # Determine file extension
        file_ext = ""
        if file.filename:
            file_ext = Path(file.filename).suffix
        
        file_path = self.upload_dir / f"upload_{upload_id}{file_ext}"
        
        # Read and save file content
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Reset file position for potential re-reading
        await file.seek(0)
        
        return file_path
    
    async def _parse_file(self, file_path: Path, file_type: str) -> List[Dict[str, Any]]:
        """Parse file content into entity data.
        
        Args:
            file_path: Path to file
            file_type: File type (yaml, csv, excel)
            
        Returns:
            List of parsed entity dictionaries
        """
        if file_type.lower() == "yaml":
            return await self._parse_yaml(file_path)
        elif file_type.lower() == "csv":
            return await self._parse_csv(file_path)
        elif file_type.lower() in ["excel", "xlsx"]:
            return await self._parse_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    async def _parse_yaml(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            List of entity dictionaries
        """
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError("YAML file must contain a list or dictionary of entities")
    
    async def _parse_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            # Try to detect dialect
            sample = f.read(1024)
            f.seek(0)
            
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel  # Default dialect
            
            reader = csv.DictReader(f, dialect=dialect)
            
            for row in reader:
                # Clean up row data
                clean_row = {}
                for key, value in row.items():
                    if key and value:  # Skip empty keys and values
                        # Clean key name
                        clean_key = key.strip().lower().replace(' ', '_')
                        
                        # Try to convert values to appropriate types
                        clean_value = self._convert_csv_value(value.strip())
                        clean_row[clean_key] = clean_value
                
                if clean_row:  # Only add non-empty rows
                    entities.append(clean_row)
        
        return entities
    
    def _convert_csv_value(self, value: str) -> Any:
        """Convert CSV string value to appropriate type.
        
        Args:
            value: String value from CSV
            
        Returns:
            Converted value
        """
        # Try boolean first
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            if '.' not in value and value.isdigit():
                return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try date formats
        for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                from datetime import datetime
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        
        # Return as string
        return value
    
    async def _parse_excel(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            List of entity dictionaries
        """
        try:
            # Try to read with openpyxl first
            df = pd.read_excel(file_path, engine='openpyxl')
        except ImportError:
            # Fallback to default engine
            df = pd.read_excel(file_path)
        
        # Clean column names
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        # Convert to list of dictionaries
        entities = []
        for _, row in df.iterrows():
            entity = {}
            for key, value in row.items():
                if pd.notna(value):  # Skip NaN values
                    # Convert numpy types to Python types
                    if hasattr(value, 'item'):
                        value = value.item()
                    entity[key] = value
            
            if entity:  # Only add non-empty entities
                entities.append(entity)
        
        return entities
    
    async def _validate_entities(self, entities_data: List[Dict[str, Any]], 
                                entity_type: Optional[str]) -> FileValidationResult:
        """Validate parsed entities.
        
        Args:
            entities_data: List of entity data dictionaries
            entity_type: Expected entity type (optional)
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        valid_entities = []
        
        for i, entity_data in enumerate(entities_data):
            try:
                # Add entity type if specified and not present
                if entity_type and 'type' not in entity_data:
                    entity_data['type'] = entity_type
                
                # Validate individual entity
                entity_errors = self.validator.validate_entity_data(entity_data)
                
                if entity_errors:
                    errors.extend([f"Entity {i+1}: {error}" for error in entity_errors])
                else:
                    valid_entities.append(entity_data)
                    
            except Exception as e:
                errors.append(f"Entity {i+1}: {str(e)}")
        
        # Generate warnings for common issues
        if len(valid_entities) < len(entities_data):
            warnings.append(f"{len(entities_data) - len(valid_entities)} entities failed validation")
        
        # Check for duplicate names within same type
        names_by_type = {}
        for entity_data in valid_entities:
            entity_type = entity_data.get('type', 'unknown')
            entity_name = entity_data.get('name', 'unnamed')
            
            if entity_type not in names_by_type:
                names_by_type[entity_type] = []
            
            if entity_name in names_by_type[entity_type]:
                warnings.append(f"Duplicate name '{entity_name}' found in {entity_type} entities")
            else:
                names_by_type[entity_type].append(entity_name)
        
        return FileValidationResult(
            is_valid=len(errors) == 0,
            entity_count=len(valid_entities),
            errors=errors,
            warnings=warnings,
            preview_entities=valid_entities[:5]  # First 5 entities as preview
        )
    
    async def _create_entities(self, entities_data: List[Dict[str, Any]], 
                             overwrite_existing: bool) -> List[str]:
        """Create entities from validated data.
        
        Args:
            entities_data: List of validated entity data
            overwrite_existing: Whether to overwrite existing entities
            
        Returns:
            List of created entity IDs
        """
        created_entity_ids = []
        
        for entity_data in entities_data:
            try:
                # Check if entity already exists (by name and type)
                existing_entity = None
                if not overwrite_existing:
                    # This would need to be implemented in the actual store
                    # existing_entity = self.store.find_entity_by_name_and_type(
                    #     entity_data.get('name'), entity_data.get('type')
                    # )
                    pass
                
                if existing_entity and not overwrite_existing:
                    continue  # Skip existing entities
                
                # Create entity through store
                # This would need to integrate with the actual entity creation system
                entity_id = await self._create_single_entity(entity_data)
                if entity_id:
                    created_entity_ids.append(entity_id)
                    
            except Exception as e:
                # Log error but continue with other entities
                print(f"Error creating entity: {str(e)}")
                continue
        
        return created_entity_ids
    
    async def _create_single_entity(self, entity_data: Dict[str, Any]) -> Optional[str]:
        """Create a single entity from data.
        
        Args:
            entity_data: Entity data dictionary
            
        Returns:
            Created entity ID or None
        """
        # This is a simplified implementation
        # In the actual system, this would need to:
        # 1. Create appropriate entity type based on entity_data['type']
        # 2. Validate against the specific entity model
        # 3. Save to the store
        # 4. Return the entity ID
        
        try:
            entity_type = entity_data.get('type', 'unknown')
            entity_id = str(uuid.uuid4())
            
            # Mock entity creation - replace with actual implementation
            # entity = self.store.create_entity(entity_type, entity_data)
            # entity_id = entity.id
            
            return entity_id
            
        except Exception as e:
            print(f"Failed to create entity: {str(e)}")
            return None
    
    def get_upload(self, upload_id: str) -> Optional[FileUploadResponse]:
        """Get upload by ID.
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            Upload response or None
        """
        return self._uploads.get(upload_id)
    
    def list_uploads(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """List all uploads with pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            
        Returns:
            Paginated upload list
        """
        uploads = list(self._uploads.values())
        uploads.sort(key=lambda u: u.created_at, reverse=True)
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_uploads = uploads[start_idx:end_idx]
        
        return {
            "uploads": page_uploads,
            "total": len(uploads),
            "page": page,
            "page_size": page_size,
            "has_next": end_idx < len(uploads)
        }
    
    async def validate_file_only(self, file: UploadFile, file_type: str, 
                                entity_type: Optional[str] = None) -> FileValidationResult:
        """Validate file without creating entities.
        
        Args:
            file: Uploaded file
            file_type: File type
            entity_type: Expected entity type
            
        Returns:
            Validation result
        """
        upload_id = str(uuid.uuid4())
        
        try:
            # Save file temporarily
            file_path = await self._save_uploaded_file(file, upload_id)
            
            # Parse and validate
            entities_data = await self._parse_file(file_path, file_type)
            validation_result = await self._validate_entities(entities_data, entity_type)
            
            # Clean up
            file_path.unlink(missing_ok=True)
            
            return validation_result
            
        except Exception as e:
            return FileValidationResult(
                is_valid=False,
                entity_count=0,
                errors=[str(e)],
                warnings=[],
                preview_entities=[]
            )
    
    def cleanup_old_uploads(self, max_age_days: int = 7):
        """Clean up old upload records.
        
        Args:
            max_age_days: Maximum age in days
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        to_delete = []
        for upload_id, upload in self._uploads.items():
            if upload.created_at < cutoff_date:
                to_delete.append(upload_id)
        
        for upload_id in to_delete:
            del self._uploads[upload_id]
    
    def get_upload_statistics(self) -> Dict[str, Any]:
        """Get upload statistics.
        
        Returns:
            Dictionary with upload statistics
        """
        uploads = list(self._uploads.values())
        
        total_uploads = len(uploads)
        successful_uploads = len([u for u in uploads if u.status == "completed"])
        failed_uploads = len([u for u in uploads if u.status in ["error", "validation_failed"]])
        
        total_entities_created = sum(len(u.created_entities) for u in uploads)
        
        # Group by file type if we tracked it
        uploads_by_status = {}
        for upload in uploads:
            status = upload.status
            if status not in uploads_by_status:
                uploads_by_status[status] = 0
            uploads_by_status[status] += 1
        
        return {
            "total_uploads": total_uploads,
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "success_rate": (successful_uploads / max(total_uploads, 1)) * 100,
            "total_entities_created": total_entities_created,
            "uploads_by_status": uploads_by_status
        }