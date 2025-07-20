"""
CashCow Web API - Main application entry point.
"""

import asyncio
import logging

from fastapi import FastAPI, WebSocket, Request
from . import create_app
from .routers import entities, calculations, scenarios, analysis, reports, files
from .websockets.handlers import (
    websocket_calculations,
    websocket_entities,
    websocket_status,
    broadcast_calculation_progress
)
from .websockets.file_integration import (
    start_websocket_file_watcher,
    stop_websocket_file_watcher
)
from .tasks import job_manager


logger = logging.getLogger(__name__)


async def _broadcast_job_progress(job_result):
    """Broadcast job progress updates via WebSocket."""
    try:
        await broadcast_calculation_progress(
            job_id=job_result.job_id,
            progress=job_result.progress,
            status=job_result.status.value,
            details={
                "message": job_result.progress_message,
                "metadata": job_result.metadata,
                "started_at": job_result.started_at,
                "duration": job_result.duration
            }
        )
    except Exception as e:
        logger.error(f"Error broadcasting job progress: {e}")


# Create the FastAPI application instance
app: FastAPI = create_app()

# Include routers with /api prefix
app.include_router(entities.router, prefix="/api")
app.include_router(calculations.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(files.router, prefix="/api")


# Application startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup handler."""
    logger.info("Starting CashCow API...")
    
    try:
        # Start job manager
        await job_manager.start()
        logger.info("Job manager started")
        
        # Start WebSocket file watcher
        await start_websocket_file_watcher()
        logger.info("WebSocket file watcher started")
        
        # Add progress callback for broadcasting job updates
        job_manager.add_progress_callback(_broadcast_job_progress)
        
        logger.info("CashCow API startup complete")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown handler."""
    logger.info("Shutting down CashCow API...")
    
    try:
        # Stop file watcher
        await stop_websocket_file_watcher()
        logger.info("WebSocket file watcher stopped")
        
        # Stop job manager
        await job_manager.stop()
        logger.info("Job manager stopped")
        
        logger.info("CashCow API shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# WebSocket endpoints
@app.websocket("/ws/calculations")
async def websocket_calculations_endpoint(websocket: WebSocket, request: Request):
    """WebSocket endpoint for calculation updates."""
    await websocket_calculations(websocket, request)


@app.websocket("/ws/entities")
async def websocket_entities_endpoint(websocket: WebSocket, request: Request):
    """WebSocket endpoint for entity updates."""
    await websocket_entities(websocket, request)


@app.websocket("/ws/status")
async def websocket_status_endpoint(websocket: WebSocket, request: Request):
    """WebSocket endpoint for status updates."""
    await websocket_status(websocket, request)


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "service": "cashcow-api",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """
    Root endpoint with basic API information.
    
    Returns:
        dict: API information
    """
    return {
        "message": "CashCow API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "api_endpoints": {
            "entities": "/entities",
            "calculations": "/calculations", 
            "scenarios": "/scenarios",
            "analysis": "/analysis",
            "reports": "/reports",
            "files": "/files"
        },
        "websockets": {
            "calculations": "/ws/calculations",
            "entities": "/ws/entities", 
            "status": "/ws/status"
        },
        "jobs_api": "/api/jobs"
    }


# Job management endpoints
@app.get("/api/jobs")
async def list_jobs():
    """List all active and recent jobs."""
    from .tasks import job_manager
    from .models.websockets import JobListResponse, JobInfo
    
    active_jobs = await job_manager.get_active_jobs()
    completed_jobs = await job_manager.get_completed_jobs(limit=20)
    
    # Convert to response models
    active_job_infos = []
    for job_result in active_jobs.values():
        job_info = JobInfo(
            job_id=job_result.job_id,
            job_type=job_result.metadata.get("job_type", "unknown"),
            status=job_result.status,
            created_at=job_result.started_at or job_result.result.started_at if hasattr(job_result, 'result') else None,
            started_at=job_result.started_at,
            completed_at=job_result.completed_at,
            progress=job_result.progress,
            progress_message=job_result.progress_message,
            metadata=job_result.metadata
        )
        active_job_infos.append(job_info)
    
    completed_job_infos = []
    for job_result in completed_jobs:
        job_info = JobInfo(
            job_id=job_result.job_id,
            job_type=job_result.metadata.get("job_type", "unknown"),
            status=job_result.status,
            created_at=job_result.started_at,
            started_at=job_result.started_at,
            completed_at=job_result.completed_at,
            progress=job_result.progress,
            progress_message=job_result.progress_message,
            metadata=job_result.metadata
        )
        completed_job_infos.append(job_info)
    
    return JobListResponse(
        active_jobs=active_job_infos,
        completed_jobs=completed_job_infos,
        total_active=len(active_job_infos),
        total_completed=len(completed_job_infos)
    )


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific job."""
    from .tasks import job_manager
    
    job_result = await job_manager.get_job_status(job_id)
    if not job_result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_result.job_id,
        "status": job_result.status.value,
        "progress": job_result.progress,
        "progress_message": job_result.progress_message,
        "result": job_result.result,
        "error": job_result.error,
        "started_at": job_result.started_at,
        "completed_at": job_result.completed_at,
        "duration": job_result.duration,
        "metadata": job_result.metadata
    }


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job."""
    from .tasks import job_manager
    
    success = await job_manager.cancel_job(job_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found or already completed")
    
    return {"message": f"Job {job_id} cancelled successfully"}


@app.get("/api/websockets/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    from .websockets.manager import connection_manager
    from .models.websockets import ConnectionStats
    
    stats = connection_manager.get_connection_stats()
    return ConnectionStats(**stats)


@app.post("/api/websockets/test-broadcast")
async def test_websocket_broadcast(message_type: str = "test", topic: str = "status"):
    """Test endpoint to broadcast WebSocket messages."""
    from .websockets.manager import connection_manager, WebSocketMessage
    import time
    
    test_message = WebSocketMessage(
        type=message_type,
        data={
            "message": f"Test broadcast at {time.strftime('%H:%M:%S')}",
            "test": True,
            "timestamp": time.time()
        }
    )
    
    await connection_manager.broadcast(test_message, topic)
    
    return {
        "success": True,
        "message": f"Broadcasted {message_type} to {topic} topic",
        "connections": len(connection_manager.subscriptions.get(topic, set()))
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)