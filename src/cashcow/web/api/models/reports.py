"""
CashCow Web API - Report models for API requests and responses.
"""

from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field
import uuid


class ReportFormat(str, Enum):
    """Available report output formats."""
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportType(str, Enum):
    """Available report types."""
    CASH_FLOW = "cash_flow"
    KPI_DASHBOARD = "kpi_dashboard"
    ENTITY_SUMMARY = "entity_summary"
    SCENARIO_COMPARISON = "scenario_comparison"
    EXECUTIVE_SUMMARY = "executive_summary"
    CUSTOM = "custom"


class ChartType(str, Enum):
    """Available chart types."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    STACKED = "stacked"
    GAUGE = "gauge"


class ReportTemplate(BaseModel):
    """Model for report template definitions."""
    id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template display name")
    description: str = Field(..., description="Template description")
    type: ReportType = Field(..., description="Report type")
    supported_formats: List[ReportFormat] = Field(..., description="Supported output formats")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Template parameters schema")
    is_custom: bool = Field(False, description="Whether this is a custom template")


class ReportParameter(BaseModel):
    """Individual report parameter definition."""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, number, date, boolean)")
    required: bool = Field(False, description="Whether parameter is required")
    default_value: Optional[Any] = Field(None, description="Default parameter value")
    description: str = Field(..., description="Parameter description")
    options: Optional[List[str]] = Field(None, description="Available options for select parameters")


class DateRange(BaseModel):
    """Date range specification."""
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    
    def model_post_init(self, __context):
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")


class ReportFilters(BaseModel):
    """Filters for report generation."""
    entity_types: Optional[List[str]] = Field(None, description="Filter by entity types")
    entity_tags: Optional[List[str]] = Field(None, description="Filter by entity tags")
    date_range: Optional[DateRange] = Field(None, description="Date range filter")
    scenario: Optional[str] = Field(None, description="Scenario name")
    include_inactive: bool = Field(False, description="Include inactive entities")


class ChartConfiguration(BaseModel):
    """Configuration for chart generation."""
    chart_type: ChartType = Field(ChartType.LINE, description="Type of chart")
    title: Optional[str] = Field(None, description="Chart title")
    width: int = Field(800, ge=200, le=2000, description="Chart width in pixels")
    height: int = Field(600, ge=200, le=2000, description="Chart height in pixels")
    color_scheme: Optional[str] = Field("default", description="Chart color scheme")
    show_legend: bool = Field(True, description="Whether to show chart legend")
    show_grid: bool = Field(True, description="Whether to show grid lines")


class ReportRequest(BaseModel):
    """Request model for generating a report."""
    template_id: str = Field(..., description="Report template ID")
    title: Optional[str] = Field(None, description="Custom report title")
    format: ReportFormat = Field(ReportFormat.HTML, description="Output format")
    filters: Optional[ReportFilters] = Field(None, description="Report filters")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Template-specific parameters")
    output_options: Dict[str, Any] = Field(default_factory=dict, description="Output formatting options")
    include_charts: bool = Field(True, description="Whether to include charts")
    include_data: bool = Field(True, description="Whether to include raw data")


class ReportGenerationStatus(str, Enum):
    """Report generation status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportResponse(BaseModel):
    """Response model for generated reports."""
    report_id: str = Field(..., description="Unique report identifier")
    title: str = Field(..., description="Report title")
    template_id: str = Field(..., description="Template used for generation")
    format: ReportFormat = Field(..., description="Report format")
    status: ReportGenerationStatus = Field(..., description="Generation status")
    created_at: datetime = Field(..., description="Report creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Report completion timestamp")
    file_path: Optional[str] = Field(None, description="Path to generated file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    download_url: Optional[str] = Field(None, description="Download URL")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional report metadata")


class ReportListResponse(BaseModel):
    """Response model for report listing."""
    reports: List[ReportResponse]
    total: int = Field(..., description="Total number of reports")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(50, description="Number of items per page")
    has_next: bool = Field(False, description="Whether there are more pages")


class CustomReportSection(BaseModel):
    """Configuration for custom report sections."""
    type: str = Field(..., description="Section type (summary, chart, table, text)")
    title: str = Field(..., description="Section title")
    content: Optional[str] = Field(None, description="Text content for text sections")
    data_source: Optional[str] = Field(None, description="Data source identifier")
    chart_config: Optional[ChartConfiguration] = Field(None, description="Chart configuration")
    table_columns: Optional[List[str]] = Field(None, description="Table columns to include")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Section-specific parameters")


class CustomReportTemplate(BaseModel):
    """Template for custom report creation."""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    sections: List[CustomReportSection] = Field(..., description="Report sections")
    global_parameters: Dict[str, Any] = Field(default_factory=dict, description="Global template parameters")


class FileUploadRequest(BaseModel):
    """Request model for file upload operations."""
    file_type: str = Field(..., description="File type (yaml, csv, excel)")
    entity_type: Optional[str] = Field(None, description="Target entity type")
    validate_only: bool = Field(False, description="Only validate, don't save")
    overwrite_existing: bool = Field(False, description="Overwrite existing entities")
    import_options: Dict[str, Any] = Field(default_factory=dict, description="Import-specific options")


class FileValidationResult(BaseModel):
    """Result of file validation."""
    is_valid: bool = Field(..., description="Whether file is valid")
    entity_count: int = Field(0, description="Number of entities found")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    preview_entities: List[Dict[str, Any]] = Field(default_factory=list, description="Preview of parsed entities")


class FileUploadResponse(BaseModel):
    """Response model for file upload operations."""
    upload_id: str = Field(..., description="Unique upload identifier")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Upload status")
    validation_result: Optional[FileValidationResult] = Field(None, description="Validation results")
    created_entities: List[str] = Field(default_factory=list, description="IDs of created entities")
    error_message: Optional[str] = Field(None, description="Error message if upload failed")
    created_at: datetime = Field(..., description="Upload timestamp")


class FileExportRequest(BaseModel):
    """Request model for file export operations."""
    format: str = Field(..., description="Export format (yaml, csv, excel, json)")
    entity_types: Optional[List[str]] = Field(None, description="Entity types to export")
    entity_ids: Optional[List[str]] = Field(None, description="Specific entity IDs to export")
    filters: Optional[ReportFilters] = Field(None, description="Export filters")
    include_metadata: bool = Field(True, description="Include entity metadata")
    template_format: bool = Field(False, description="Export as template format")


class FileExportResponse(BaseModel):
    """Response model for file export operations."""
    export_id: str = Field(..., description="Unique export identifier")
    file_name: str = Field(..., description="Generated file name")
    file_path: str = Field(..., description="File path")
    file_size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Export format")
    entity_count: int = Field(..., description="Number of exported entities")
    download_url: str = Field(..., description="Download URL")
    created_at: datetime = Field(..., description="Export timestamp")
    expires_at: Optional[datetime] = Field(None, description="Download expiration")


class ReportTemplateListResponse(BaseModel):
    """Response model for listing available report templates."""
    templates: List[ReportTemplate]
    custom_templates: List[CustomReportTemplate] = Field(default_factory=list)


class FileTemplateInfo(BaseModel):
    """Information about file templates."""
    entity_type: str = Field(..., description="Entity type")
    format: str = Field(..., description="File format")
    template_name: str = Field(..., description="Template file name")
    description: str = Field(..., description="Template description")
    sample_data: bool = Field(False, description="Whether template includes sample data")


class FileTemplateListResponse(BaseModel):
    """Response model for listing file templates."""
    templates: List[FileTemplateInfo]


# Scenario-specific models
class ScenarioComparisonRequest(BaseModel):
    """Request for scenario comparison report."""
    scenarios: List[str] = Field(..., description="Scenario names to compare")
    date_range: Optional[DateRange] = Field(None, description="Date range for comparison")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to compare")
    format: ReportFormat = Field(ReportFormat.HTML, description="Output format")


class KPIDashboardRequest(BaseModel):
    """Request for KPI dashboard report."""
    kpi_categories: Optional[List[str]] = Field(None, description="KPI categories to include")
    date_range: Optional[DateRange] = Field(None, description="Date range for calculations")
    comparison_period: Optional[DateRange] = Field(None, description="Comparison period")
    format: ReportFormat = Field(ReportFormat.HTML, description="Output format")
    chart_config: Optional[ChartConfiguration] = Field(None, description="Chart configuration")


class EntitySummaryRequest(BaseModel):
    """Request for entity summary report."""
    group_by: str = Field("type", description="How to group entities (type, tag, status)")
    include_financial_impact: bool = Field(True, description="Include financial impact analysis")
    format: ReportFormat = Field(ReportFormat.HTML, description="Output format")
    filters: Optional[ReportFilters] = Field(None, description="Entity filters")


# Progress tracking models
class ReportProgress(BaseModel):
    """Model for tracking report generation progress."""
    report_id: str = Field(..., description="Report identifier")
    status: ReportGenerationStatus = Field(..., description="Current status")
    progress_percentage: int = Field(0, ge=0, le=100, description="Progress percentage")
    current_step: str = Field(..., description="Current processing step")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error_details: Optional[str] = Field(None, description="Detailed error information")


class BatchReportRequest(BaseModel):
    """Request for generating multiple reports in batch."""
    reports: List[ReportRequest] = Field(..., description="List of reports to generate")
    batch_name: Optional[str] = Field(None, description="Batch identifier name")
    notify_on_completion: bool = Field(False, description="Send notification when complete")


class BatchReportResponse(BaseModel):
    """Response for batch report generation."""
    batch_id: str = Field(..., description="Unique batch identifier")
    batch_name: Optional[str] = Field(None, description="Batch name")
    total_reports: int = Field(..., description="Total number of reports in batch")
    status: str = Field(..., description="Batch status")
    created_at: datetime = Field(..., description="Batch creation time")
    reports: List[ReportResponse] = Field(..., description="Individual report statuses")


# Error models
class ReportError(BaseModel):
    """Model for report generation errors."""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    suggestions: List[str] = Field(default_factory=list, description="Suggested fixes")


# Validation models
class ReportValidationResponse(BaseModel):
    """Response model for report validation."""
    valid: bool = Field(..., description="Whether report configuration is valid")
    errors: List[ReportError] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    estimated_size: Optional[int] = Field(None, description="Estimated output file size")
    estimated_duration: Optional[int] = Field(None, description="Estimated generation time in seconds")