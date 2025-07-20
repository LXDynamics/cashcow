"""
CashCow Web API - File export functionality.
"""

import csv
import json
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

from cashcow.storage.database import EntityStore
from ..models.reports import (
    FileExportRequest, FileExportResponse, FileTemplateInfo
)


class FileExporter:
    """Handles entity export to various file formats."""
    
    def __init__(self, store: EntityStore, export_dir: str = None):
        """Initialize file exporter.
        
        Args:
            store: Entity store instance
            export_dir: Directory for export files
        """
        self.store = store
        
        if export_dir is None:
            self.export_dir = Path(tempfile.gettempdir()) / "cashcow_exports"
        else:
            self.export_dir = Path(export_dir)
        
        self.export_dir.mkdir(exist_ok=True)
        
        # Track exports
        self._exports: Dict[str, FileExportResponse] = {}
    
    async def export_entities(self, request: FileExportRequest) -> FileExportResponse:
        """Export entities based on request.
        
        Args:
            request: Export request
            
        Returns:
            Export response with file information
        """
        export_id = str(uuid.uuid4())
        
        try:
            # Get entities based on filters
            entities = await self._get_entities_for_export(request)
            
            # Generate export file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"cashcow_entities_{timestamp}"
            
            if request.template_format:
                base_filename = f"cashcow_template_{timestamp}"
            
            file_path = await self._export_to_format(
                entities, request.format, base_filename, request
            )
            
            # Create response
            response = FileExportResponse(
                export_id=export_id,
                file_name=file_path.name,
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                format=request.format,
                entity_count=len(entities),
                download_url=f"/api/files/exports/{export_id}",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7)
            )
            
            self._exports[export_id] = response
            return response
            
        except Exception as e:
            # Create error response
            error_response = FileExportResponse(
                export_id=export_id,
                file_name="export_failed",
                file_path="",
                file_size=0,
                format=request.format,
                entity_count=0,
                download_url="",
                created_at=datetime.now()
            )
            
            self._exports[export_id] = error_response
            raise e
    
    async def _get_entities_for_export(self, request: FileExportRequest) -> List[Any]:
        """Get entities for export based on request filters.
        
        Args:
            request: Export request
            
        Returns:
            List of entities to export
        """
        # Start with all entities
        entities = self.store.get_all_entities()
        
        # Filter by specific entity IDs if provided
        if request.entity_ids:
            entities = [e for e in entities if e.id in request.entity_ids]
        
        # Filter by entity types if provided
        if request.entity_types:
            entities = [e for e in entities if e.type in request.entity_types]
        
        # Apply additional filters if provided
        if request.filters:
            if request.filters.entity_types:
                entities = [e for e in entities if e.type in request.filters.entity_types]
            
            if request.filters.entity_tags:
                entities = [e for e in entities 
                           if any(tag in e.tags for tag in request.filters.entity_tags)]
            
            if request.filters.date_range:
                entities = [e for e in entities 
                           if (e.start_date >= request.filters.date_range.start_date and
                               e.start_date <= request.filters.date_range.end_date)]
            
            if not request.filters.include_inactive:
                entities = [e for e in entities if e.is_active()]
        
        return entities
    
    async def _export_to_format(self, entities: List[Any], format_type: str, 
                               base_filename: str, request: FileExportRequest) -> Path:
        """Export entities to specified format.
        
        Args:
            entities: List of entities to export
            format_type: Export format
            base_filename: Base filename without extension
            request: Export request
            
        Returns:
            Path to exported file
        """
        if format_type == "yaml":
            return await self._export_yaml(entities, base_filename, request)
        elif format_type == "csv":
            return await self._export_csv(entities, base_filename, request)
        elif format_type == "excel":
            return await self._export_excel(entities, base_filename, request)
        elif format_type == "json":
            return await self._export_json(entities, base_filename, request)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def _export_yaml(self, entities: List[Any], base_filename: str, 
                          request: FileExportRequest) -> Path:
        """Export entities to YAML format.
        
        Args:
            entities: List of entities
            base_filename: Base filename
            request: Export request
            
        Returns:
            Path to YAML file
        """
        file_path = self.export_dir / f"{base_filename}.yaml"
        
        # Convert entities to dictionaries
        export_data = []
        for entity in entities:
            entity_data = entity.model_dump() if hasattr(entity, 'model_dump') else entity.__dict__
            
            # Remove metadata if not requested
            if not request.include_metadata:
                entity_data.pop("id", None)
                entity_data.pop("created_at", None)
                entity_data.pop("updated_at", None)
            
            # Handle template format
            if request.template_format:
                entity_data = self._convert_to_template_format(entity_data)
            
            export_data.append(entity_data)
        
        # Write YAML file
        with open(file_path, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False, 
                     allow_unicode=True, default_style=None)
        
        return file_path
    
    async def _export_csv(self, entities: List[Any], base_filename: str, 
                         request: FileExportRequest) -> Path:
        """Export entities to CSV format.
        
        Args:
            entities: List of entities
            base_filename: Base filename
            request: Export request
            
        Returns:
            Path to CSV file
        """
        file_path = self.export_dir / f"{base_filename}.csv"
        
        if not entities:
            # Create empty CSV file
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["No entities found"])
            return file_path
        
        # Convert entities to flat dictionaries
        flattened_entities = []
        for entity in entities:
            entity_data = entity.model_dump() if hasattr(entity, 'model_dump') else entity.__dict__
            
            # Remove metadata if not requested
            if not request.include_metadata:
                entity_data.pop("id", None)
                entity_data.pop("created_at", None)
                entity_data.pop("updated_at", None)
            
            # Flatten nested structures
            flat_data = self._flatten_dict(entity_data)
            
            # Handle template format
            if request.template_format:
                flat_data = self._convert_to_template_format(flat_data)
            
            flattened_entities.append(flat_data)
        
        # Create DataFrame and export
        df = pd.DataFrame(flattened_entities)
        df.to_csv(file_path, index=False)
        
        return file_path
    
    async def _export_excel(self, entities: List[Any], base_filename: str, 
                           request: FileExportRequest) -> Path:
        """Export entities to Excel format.
        
        Args:
            entities: List of entities
            base_filename: Base filename
            request: Export request
            
        Returns:
            Path to Excel file
        """
        file_path = self.export_dir / f"{base_filename}.xlsx"
        
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            
            # Group entities by type
            entities_by_type = {}
            for entity in entities:
                entity_data = entity.model_dump() if hasattr(entity, 'model_dump') else entity.__dict__
                entity_type = entity_data.get('type', 'unknown')
                
                # Remove metadata if not requested
                if not request.include_metadata:
                    entity_data.pop("id", None)
                    entity_data.pop("created_at", None)
                    entity_data.pop("updated_at", None)
                
                # Handle template format
                if request.template_format:
                    entity_data = self._convert_to_template_format(entity_data)
                
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(entity_data)
            
            # Create Excel workbook
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for entity_type, type_entities in entities_by_type.items():
                    # Flatten entities for tabular format
                    flattened_entities = [self._flatten_dict(e) for e in type_entities]
                    df = pd.DataFrame(flattened_entities)
                    
                    # Write to sheet (limit sheet name to 31 chars)
                    sheet_name = entity_type[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Format the sheet
                    worksheet = writer.sheets[sheet_name]
                    
                    # Header formatting
                    header_font = Font(bold=True, color="FFFFFF")
                    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                    
                    for cell in worksheet[1]:  # First row
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = Alignment(horizontal="center")
                    
                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
        
        except ImportError:
            # Fallback to CSV if openpyxl not available
            csv_path = await self._export_csv(entities, base_filename, request)
            # Rename to xlsx for consistency
            file_path = csv_path.with_suffix('.xlsx')
            csv_path.rename(file_path)
        
        return file_path
    
    async def _export_json(self, entities: List[Any], base_filename: str, 
                          request: FileExportRequest) -> Path:
        """Export entities to JSON format.
        
        Args:
            entities: List of entities
            base_filename: Base filename
            request: Export request
            
        Returns:
            Path to JSON file
        """
        file_path = self.export_dir / f"{base_filename}.json"
        
        # Convert entities to dictionaries
        export_data = []
        for entity in entities:
            entity_data = entity.model_dump() if hasattr(entity, 'model_dump') else entity.__dict__
            
            # Remove metadata if not requested
            if not request.include_metadata:
                entity_data.pop("id", None)
                entity_data.pop("created_at", None)
                entity_data.pop("updated_at", None)
            
            # Handle template format
            if request.template_format:
                entity_data = self._convert_to_template_format(entity_data)
            
            export_data.append(entity_data)
        
        # Write JSON file
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str, ensure_ascii=False)
        
        return file_path
    
    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary.
        
        Args:
            data: Dictionary to flatten
            parent_key: Parent key prefix
            sep: Separator for nested keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to semicolon-separated strings
                items.append((new_key, "; ".join(str(item) for item in v)))
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    def _convert_to_template_format(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert entity data to template format.
        
        Args:
            entity_data: Entity data
            
        Returns:
            Template formatted data
        """
        # For template format, replace actual values with placeholder examples
        template_data = entity_data.copy()
        
        # Replace monetary values with examples
        for key, value in template_data.items():
            if key in ['salary', 'amount', 'cost', 'monthly_cost', 'total_budget']:
                if isinstance(value, (int, float)):
                    template_data[key] = 50000  # Example value
            elif key in ['name']:
                template_data[key] = f"Example {entity_data.get('type', 'Entity').title()}"
            elif key in ['start_date', 'end_date', 'purchase_date']:
                if value:
                    template_data[key] = "2024-01-01"
            elif key == 'notes':
                template_data[key] = "Add your notes here"
            elif key == 'tags':
                template_data[key] = ["tag1", "tag2"]
        
        return template_data
    
    def get_export(self, export_id: str) -> Optional[FileExportResponse]:
        """Get export by ID.
        
        Args:
            export_id: Export identifier
            
        Returns:
            Export response or None
        """
        return self._exports.get(export_id)
    
    def list_exports(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """List all exports with pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            
        Returns:
            Paginated export list
        """
        exports = list(self._exports.values())
        exports.sort(key=lambda e: e.created_at, reverse=True)
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_exports = exports[start_idx:end_idx]
        
        return {
            "exports": page_exports,
            "total": len(exports),
            "page": page,
            "page_size": page_size,
            "has_next": end_idx < len(exports)
        }
    
    def cleanup_old_exports(self, max_age_days: int = 7):
        """Clean up old export files and records.
        
        Args:
            max_age_days: Maximum age in days
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        to_delete = []
        for export_id, export in self._exports.items():
            if export.created_at < cutoff_date:
                # Delete file if it exists
                try:
                    Path(export.file_path).unlink(missing_ok=True)
                except Exception:
                    pass  # Ignore file deletion errors
                
                to_delete.append(export_id)
        
        for export_id in to_delete:
            del self._exports[export_id]
    
    def get_available_templates(self) -> List[FileTemplateInfo]:
        """Get list of available file templates.
        
        Returns:
            List of template information
        """
        templates = []
        
        # Entity type templates
        entity_types = [
            "employee", "grant", "investment", "sale", "service",
            "facility", "software", "equipment", "project"
        ]
        
        formats = ["yaml", "csv", "excel", "json"]
        
        for entity_type in entity_types:
            for format_type in formats:
                templates.append(FileTemplateInfo(
                    entity_type=entity_type,
                    format=format_type,
                    template_name=f"{entity_type}_template.{format_type}",
                    description=f"Template for {entity_type} entities in {format_type.upper()} format",
                    sample_data=True
                ))
        
        return templates
    
    async def generate_template_file(self, entity_type: str, format_type: str, 
                                   include_sample: bool = True) -> Path:
        """Generate template file for entity type.
        
        Args:
            entity_type: Entity type
            format_type: File format
            include_sample: Include sample data
            
        Returns:
            Path to generated template file
        """
        from .validators import FileValidator
        
        validator = FileValidator()
        
        # Get template data
        template_data = validator.get_entity_template(entity_type)
        
        if include_sample:
            # Add a few sample entities
            sample_entities = [template_data]
            
            # Add variations for sample data
            for i in range(2):
                sample_entity = template_data.copy()
                sample_entity["name"] = f"Example {entity_type.title()} {i+2}"
                if "salary" in sample_entity:
                    sample_entity["salary"] = template_data["salary"] + (i * 10000)
                if "amount" in sample_entity:
                    sample_entity["amount"] = template_data["amount"] + (i * 50000)
                sample_entities.append(sample_entity)
        else:
            # Just the template structure
            sample_entities = [template_data]
        
        # Create temporary export request
        request = FileExportRequest(
            format=format_type,
            entity_types=[entity_type],
            include_metadata=False,
            template_format=True
        )
        
        # Generate file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{entity_type}_template_{timestamp}"
        
        # Mock entities for template generation
        class MockEntity:
            def __init__(self, data):
                for k, v in data.items():
                    setattr(self, k, v)
            
            def model_dump(self):
                return {k: v for k, v in self.__dict__.items()}
        
        mock_entities = [MockEntity(data) for data in sample_entities]
        
        return await self._export_to_format(mock_entities, format_type, base_filename, request)
    
    def get_export_statistics(self) -> Dict[str, Any]:
        """Get export statistics.
        
        Returns:
            Dictionary with export statistics
        """
        exports = list(self._exports.values())
        
        total_exports = len(exports)
        total_entities_exported = sum(e.entity_count for e in exports)
        
        # Group by format
        exports_by_format = {}
        for export in exports:
            format_type = export.format
            if format_type not in exports_by_format:
                exports_by_format[format_type] = 0
            exports_by_format[format_type] += 1
        
        # Calculate total file size
        total_file_size = sum(e.file_size for e in exports)
        
        return {
            "total_exports": total_exports,
            "total_entities_exported": total_entities_exported,
            "exports_by_format": exports_by_format,
            "total_file_size_bytes": total_file_size,
            "average_entities_per_export": total_entities_exported / max(total_exports, 1)
        }