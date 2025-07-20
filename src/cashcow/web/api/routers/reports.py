"""
CashCow Web API - Reports endpoints.
"""

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse

from cashcow.engine.cashflow import CashFlowEngine
from cashcow.engine.kpis import KPICalculator
from cashcow.storage.database import EntityStore
from ..dependencies import get_store, get_engine, get_kpi_calculator
from ..models.reports import (
    ReportRequest, ReportResponse, ReportFormat, ReportType,
    ReportTemplateListResponse, ReportListResponse, ReportProgress,
    CustomReportTemplate, KPIDashboardRequest, ScenarioComparisonRequest,
    EntitySummaryRequest, ReportValidationResponse, BatchReportRequest,
    BatchReportResponse
)
from ..reports import WebReportGenerator, ReportTemplateManager

router = APIRouter(prefix="/reports", tags=["reports"])

# Global instances (in production, these would be properly injected)
_report_generator: Optional[WebReportGenerator] = None
_template_manager: Optional[ReportTemplateManager] = None


def get_report_generator(
    store: EntityStore = Depends(get_store),
    engine: CashFlowEngine = Depends(get_engine),
    kpi_calculator: KPICalculator = Depends(get_kpi_calculator)
) -> WebReportGenerator:
    """Get report generator instance."""
    global _report_generator
    if _report_generator is None:
        _report_generator = WebReportGenerator(store, engine, kpi_calculator)
    return _report_generator


def get_template_manager() -> ReportTemplateManager:
    """Get template manager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = ReportTemplateManager()
    return _template_manager


@router.get("/templates", response_model=ReportTemplateListResponse)
async def list_report_templates(
    template_manager: ReportTemplateManager = Depends(get_template_manager)
):
    """List all available report templates."""
    templates = template_manager.list_templates()
    return ReportTemplateListResponse(templates=templates)


@router.get("/templates/{template_id}")
async def get_report_template(
    template_id: str,
    template_manager: ReportTemplateManager = Depends(get_template_manager)
):
    """Get specific report template details."""
    template = template_manager.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {template_id}"
        )
    return template


@router.get("/templates/{template_id}/preview")
async def get_template_preview(
    template_id: str,
    template_manager: ReportTemplateManager = Depends(get_template_manager)
):
    """Get template preview information."""
    preview = template_manager.get_template_preview(template_id)
    if not preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {template_id}"
        )
    return preview


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    generator: WebReportGenerator = Depends(get_report_generator),
    template_manager: ReportTemplateManager = Depends(get_template_manager)
):
    """Generate a new report."""
    # Validate template exists
    template = template_manager.get_template(request.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown template: {request.template_id}"
        )
    
    # Validate template parameters
    validation_errors = template_manager.validate_template_parameters(
        request.template_id, request.parameters
    )
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parameter validation errors: {', '.join(validation_errors)}"
        )
    
    # Generate report
    try:
        report = await generator.generate_report(request)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )


@router.post("/validate", response_model=ReportValidationResponse)
async def validate_report_request(
    request: ReportRequest,
    template_manager: ReportTemplateManager = Depends(get_template_manager)
):
    """Validate a report request without generating the report."""
    errors = []
    warnings = []
    
    # Validate template exists
    template = template_manager.get_template(request.template_id)
    if not template:
        errors.append(f"Unknown template: {request.template_id}")
        return ReportValidationResponse(valid=False, errors=errors, warnings=warnings)
    
    # Validate template parameters
    param_errors = template_manager.validate_template_parameters(
        request.template_id, request.parameters
    )
    errors.extend(param_errors)
    
    # Validate format compatibility
    if request.format not in template["supported_formats"]:
        errors.append(f"Format {request.format} not supported by template {request.template_id}")
    
    # Generate warnings for potential issues
    if request.parameters.get("forecast_months", 0) > 36:
        warnings.append("Forecasting beyond 36 months may be less accurate")
    
    return ReportValidationResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        estimated_size=1024000,  # Mock estimation
        estimated_duration=30    # Mock estimation in seconds
    )


@router.get("", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    format_filter: Optional[ReportFormat] = Query(None, description="Filter by format"),
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """List all generated reports with pagination."""
    result = generator.list_reports(page, page_size)
    
    # Apply filters if provided
    reports = result["reports"]
    
    if status_filter:
        reports = [r for r in reports if r.status == status_filter]
    
    if format_filter:
        reports = [r for r in reports if r.format == format_filter]
    
    return ReportListResponse(
        reports=reports,
        total=len(reports),
        page=page,
        page_size=page_size,
        has_next=result["has_next"]
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """Get specific report by ID."""
    report = generator.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}"
        )
    return report


@router.get("/{report_id}/progress", response_model=ReportProgress)
async def get_report_progress(
    report_id: str,
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """Get report generation progress."""
    progress = generator.get_report_progress(report_id)
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report progress not found: {report_id}"
        )
    return progress


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """Download generated report file."""
    report = generator.get_report(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}"
        )
    
    if not report.file_path or not Path(report.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )
    
    file_path = Path(report.file_path)
    
    # Determine media type based on format
    media_type_map = {
        ReportFormat.HTML: "text/html",
        ReportFormat.PDF: "application/pdf",
        ReportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ReportFormat.CSV: "text/csv",
        ReportFormat.JSON: "application/json"
    }
    
    media_type = media_type_map.get(report.format, "application/octet-stream")
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name,
        headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """Delete a report and its associated files."""
    success = generator.delete_report(report_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}"
        )
    
    return {"message": "Report deleted successfully"}


@router.post("/kpi-dashboard", response_model=ReportResponse)
async def generate_kpi_dashboard(
    request: KPIDashboardRequest,
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """Generate KPI dashboard report."""
    # Convert to standard report request
    report_request = ReportRequest(
        template_id="kpi_dashboard",
        title="KPI Dashboard",
        format=request.format,
        parameters={
            "kpi_categories": request.kpi_categories,
            "comparison_period": request.comparison_period,
            "chart_config": request.chart_config.model_dump() if request.chart_config else None
        }
    )
    
    if request.date_range:
        from ..models.reports import ReportFilters
        report_request.filters = ReportFilters(date_range=request.date_range)
    
    return await generator.generate_report(report_request)


@router.post("/scenario-comparison", response_model=ReportResponse)
async def generate_scenario_comparison(
    request: ScenarioComparisonRequest,
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """Generate scenario comparison report."""
    report_request = ReportRequest(
        template_id="scenario_comparison",
        title="Scenario Comparison",
        format=request.format,
        parameters={
            "scenarios": request.scenarios,
            "comparison_metrics": request.metrics
        }
    )
    
    if request.date_range:
        from ..models.reports import ReportFilters
        report_request.filters = ReportFilters(date_range=request.date_range)
    
    return await generator.generate_report(report_request)


@router.post("/entity-summary", response_model=ReportResponse)
async def generate_entity_summary(
    request: EntitySummaryRequest,
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """Generate entity summary report."""
    report_request = ReportRequest(
        template_id="entity_summary",
        title="Entity Summary",
        format=request.format,
        filters=request.filters,
        parameters={
            "group_by": request.group_by,
            "include_financial_impact": request.include_financial_impact
        }
    )
    
    return await generator.generate_report(report_request)


@router.post("/custom", response_model=ReportResponse)
async def generate_custom_report(
    template: CustomReportTemplate,
    format: ReportFormat = ReportFormat.HTML,
    generator: WebReportGenerator = Depends(get_report_generator),
    template_manager: ReportTemplateManager = Depends(get_template_manager)
):
    """Generate custom report from template configuration."""
    # Create custom template
    template_id = template_manager.create_custom_template({
        "name": template.name,
        "description": template.description,
        "type": ReportType.CUSTOM,
        "supported_formats": [format],
        "parameters": {
            "template_config": {
                "name": "template_config",
                "type": "object",
                "required": True,
                "description": "Custom template configuration"
            }
        }
    })
    
    # Generate report using custom template
    report_request = ReportRequest(
        template_id=template_id,
        title=template.name,
        format=format,
        parameters={
            "template_config": {
                "title": template.name,
                "sections": [section.model_dump() for section in template.sections]
            }
        }
    )
    
    return await generator.generate_report(report_request)


@router.post("/batch", response_model=BatchReportResponse)
async def generate_batch_reports(
    request: BatchReportRequest,
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """Generate multiple reports in batch."""
    batch_id = str(uuid.uuid4())
    
    # Generate all reports
    generated_reports = []
    for report_request in request.reports:
        try:
            report = await generator.generate_report(report_request)
            generated_reports.append(report)
        except Exception as e:
            # Create error report response
            error_report = ReportResponse(
                report_id=str(uuid.uuid4()),
                title=report_request.title or "Failed Report",
                template_id=report_request.template_id,
                format=report_request.format,
                status="failed",
                created_at=generator._reports[list(generator._reports.keys())[0]].created_at,
                error_message=str(e)
            )
            generated_reports.append(error_report)
    
    return BatchReportResponse(
        batch_id=batch_id,
        batch_name=request.batch_name,
        total_reports=len(request.reports),
        status="completed",
        created_at=generated_reports[0].created_at if generated_reports else None,
        reports=generated_reports
    )


@router.post("/cleanup")
async def cleanup_old_reports(
    max_age_days: int = Query(7, ge=1, le=365, description="Maximum age in days"),
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """Clean up old reports and files."""
    generator.cleanup_old_reports(max_age_days)
    return {"message": f"Cleaned up reports older than {max_age_days} days"}


@router.get("/statistics/summary")
async def get_report_statistics(
    generator: WebReportGenerator = Depends(get_report_generator)
):
    """Get report generation statistics."""
    reports = list(generator._reports.values())
    
    total_reports = len(reports)
    completed_reports = len([r for r in reports if r.status == "completed"])
    failed_reports = len([r for r in reports if r.status == "failed"])
    
    reports_by_format = {}
    for report in reports:
        format_name = report.format
        if format_name not in reports_by_format:
            reports_by_format[format_name] = 0
        reports_by_format[format_name] += 1
    
    reports_by_template = {}
    for report in reports:
        template_id = report.template_id
        if template_id not in reports_by_template:
            reports_by_template[template_id] = 0
        reports_by_template[template_id] += 1
    
    return {
        "total_reports": total_reports,
        "completed_reports": completed_reports,
        "failed_reports": failed_reports,
        "success_rate": (completed_reports / max(total_reports, 1)) * 100,
        "reports_by_format": reports_by_format,
        "reports_by_template": reports_by_template
    }


# Template management endpoints
@router.post("/templates/custom", response_model=Dict[str, str])
async def create_custom_template(
    template: CustomReportTemplate,
    template_manager: ReportTemplateManager = Depends(get_template_manager)
):
    """Create a new custom report template."""
    template_id = template_manager.create_custom_template({
        "name": template.name,
        "description": template.description,
        "type": ReportType.CUSTOM,
        "supported_formats": [ReportFormat.HTML],
        "parameters": template.global_parameters
    })
    
    return {"template_id": template_id, "message": "Custom template created successfully"}


@router.put("/templates/custom/{template_id}")
async def update_custom_template(
    template_id: str,
    template: CustomReportTemplate,
    template_manager: ReportTemplateManager = Depends(get_template_manager)
):
    """Update an existing custom template."""
    success = template_manager.update_custom_template(template_id, {
        "name": template.name,
        "description": template.description,
        "parameters": template.global_parameters
    })
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Custom template not found: {template_id}"
        )
    
    return {"message": "Custom template updated successfully"}


@router.delete("/templates/custom/{template_id}")
async def delete_custom_template(
    template_id: str,
    template_manager: ReportTemplateManager = Depends(get_template_manager)
):
    """Delete a custom template."""
    success = template_manager.delete_custom_template(template_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Custom template not found: {template_id}"
        )
    
    return {"message": "Custom template deleted successfully"}