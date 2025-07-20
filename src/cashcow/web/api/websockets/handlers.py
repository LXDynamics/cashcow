"""
WebSocket endpoint handlers for real-time CashCow updates.
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect, Request

from .manager import connection_manager, WebSocketMessage


logger = logging.getLogger(__name__)


async def websocket_calculations(websocket: WebSocket, request: Request):
    """
    WebSocket endpoint for real-time calculation progress updates.
    
    Handles:
    - Monte Carlo simulation progress
    - Financial model calculation updates
    - KPI recalculation notifications
    
    Args:
        websocket: WebSocket connection
        request: HTTP request context
    """
    client_ip = request.client.host
    connection_id = None
    
    try:
        # Connect and subscribe to calculations topic
        connection_id = await connection_manager.connect(websocket, client_ip)
        await connection_manager.subscribe(connection_id, "calculations")
        
        # Send welcome message
        welcome = WebSocketMessage(
            type="connected",
            data={
                "connection_id": connection_id,
                "topic": "calculations",
                "message": "Connected to calculation updates"
            }
        )
        await connection_manager.send_message(connection_id, welcome)
        
        # Listen for incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await connection_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from {connection_id}: {e}")
            except Exception as e:
                logger.error(f"Error handling message from {connection_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in calculations WebSocket: {e}")
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


async def websocket_entities(websocket: WebSocket, request: Request):
    """
    WebSocket endpoint for entity file change notifications.
    
    Handles:
    - YAML file creation/modification/deletion
    - Entity validation status updates
    - Real-time entity list updates
    
    Args:
        websocket: WebSocket connection
        request: HTTP request context
    """
    client_ip = request.client.host
    connection_id = None
    
    try:
        # Connect and subscribe to entities topic
        connection_id = await connection_manager.connect(websocket, client_ip)
        await connection_manager.subscribe(connection_id, "entities")
        
        # Send welcome message
        welcome = WebSocketMessage(
            type="connected",
            data={
                "connection_id": connection_id,
                "topic": "entities",
                "message": "Connected to entity updates"
            }
        )
        await connection_manager.send_message(connection_id, welcome)
        
        # Listen for incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await connection_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from {connection_id}: {e}")
            except Exception as e:
                logger.error(f"Error handling message from {connection_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in entities WebSocket: {e}")
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


async def websocket_status(websocket: WebSocket, request: Request):
    """
    WebSocket endpoint for system status and health updates.
    
    Handles:
    - System health status
    - Performance metrics
    - Error notifications
    - Service availability updates
    
    Args:
        websocket: WebSocket connection
        request: HTTP request context
    """
    client_ip = request.client.host
    connection_id = None
    
    try:
        # Connect and subscribe to status topic
        connection_id = await connection_manager.connect(websocket, client_ip)
        await connection_manager.subscribe(connection_id, "status")
        
        # Send welcome message with current status
        welcome = WebSocketMessage(
            type="connected",
            data={
                "connection_id": connection_id,
                "topic": "status",
                "message": "Connected to status updates",
                "system_status": "healthy"
            }
        )
        await connection_manager.send_message(connection_id, welcome)
        
        # Start periodic status updates
        asyncio.create_task(_send_periodic_status(connection_id))
        
        # Listen for incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await connection_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from {connection_id}: {e}")
            except Exception as e:
                logger.error(f"Error handling message from {connection_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in status WebSocket: {e}")
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


async def _send_periodic_status(connection_id: str):
    """
    Send periodic status updates to a connection.
    
    Args:
        connection_id: Connection ID to send updates to
    """
    try:
        while connection_id in connection_manager.active_connections:
            # Get system status
            stats = connection_manager.get_connection_stats()
            
            status_update = WebSocketMessage(
                type="status_update",
                data={
                    "system_status": "healthy",
                    "active_connections": stats["total_connections"],
                    "memory_usage": _get_memory_usage(),
                    "uptime": _get_uptime()
                }
            )
            
            await connection_manager.send_message(connection_id, status_update)
            await asyncio.sleep(30)  # Send every 30 seconds
            
    except Exception as e:
        logger.error(f"Error sending periodic status to {connection_id}: {e}")


def _get_memory_usage() -> dict:
    """Get memory usage statistics."""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            "rss": memory_info.rss,
            "vms": memory_info.vms,
            "percent": process.memory_percent()
        }
    except ImportError:
        return {"error": "psutil not available"}
    except Exception as e:
        return {"error": str(e)}


def _get_uptime() -> float:
    """Get application uptime in seconds."""
    import time
    # This would be better tracked from application start time
    # For now, just return a placeholder
    return time.time() % 86400  # Seconds since midnight


# Helper functions for broadcasting notifications

async def broadcast_calculation_progress(job_id: str, progress: float, status: str, details: dict = None):
    """
    Broadcast calculation progress to all subscribers.
    
    Args:
        job_id: Unique job identifier
        progress: Progress percentage (0.0 to 1.0)
        status: Job status (running, completed, failed)
        details: Additional job details
    """
    message = WebSocketMessage(
        type="calculation_progress",
        data={
            "job_id": job_id,
            "progress": progress,
            "status": status,
            "details": details or {}
        }
    )
    await connection_manager.broadcast(message, topic="calculations")


async def broadcast_entity_change(event_type: str, file_path: str, entity_data: dict = None):
    """
    Broadcast entity file changes to all subscribers.
    
    Args:
        event_type: Type of change (created, modified, deleted)
        file_path: Path to the changed file
        entity_data: Entity data (if available)
    """
    message = WebSocketMessage(
        type="entity_change",
        data={
            "event_type": event_type,
            "file_path": file_path,
            "entity_data": entity_data
        }
    )
    await connection_manager.broadcast(message, topic="entities")


async def broadcast_validation_error(file_path: str, errors: list):
    """
    Broadcast validation errors to entity subscribers.
    
    Args:
        file_path: Path to the file with validation errors
        errors: List of validation error messages
    """
    message = WebSocketMessage(
        type="validation_error",
        data={
            "file_path": file_path,
            "errors": errors
        }
    )
    await connection_manager.broadcast(message, topic="entities")


async def broadcast_system_alert(level: str, message_text: str, details: dict = None):
    """
    Broadcast system alerts to status subscribers.
    
    Args:
        level: Alert level (info, warning, error, critical)
        message_text: Alert message
        details: Additional alert details
    """
    message = WebSocketMessage(
        type="system_alert",
        data={
            "level": level,
            "message": message_text,
            "details": details or {}
        }
    )
    await connection_manager.broadcast(message, topic="status")