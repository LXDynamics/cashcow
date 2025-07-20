"""
Integration between file watching and WebSocket notifications.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional

from ....watchers import EntityFileWatcher
from .handlers import broadcast_entity_change, broadcast_validation_error
from .manager import connection_manager


logger = logging.getLogger(__name__)


class WebSocketFileWatcher:
    """File watcher that broadcasts changes via WebSocket."""
    
    def __init__(self, entities_dir: str = "entities"):
        """
        Initialize WebSocket-enabled file watcher.
        
        Args:
            entities_dir: Directory to watch for entity files
        """
        self.entities_dir = entities_dir
        self.watcher: Optional[EntityFileWatcher] = None
        self.running = False
    
    async def start(self):
        """Start the file watcher with WebSocket integration."""
        if self.running:
            return
        
        try:
            # Create file watcher
            self.watcher = EntityFileWatcher(
                entities_dir=self.entities_dir,
                auto_validate=True,
                git_integration=True
            )
            
            # Add callbacks for WebSocket notifications
            self.watcher.add_change_callback(self._on_file_change)
            self.watcher.add_validation_error_callback(self._on_validation_error)
            
            # Start watching
            self.watcher.start()
            self.running = True
            
            logger.info(f"Started WebSocket file watcher for {self.entities_dir}")
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket file watcher: {e}")
            raise
    
    async def stop(self):
        """Stop the file watcher."""
        if not self.running:
            return
        
        try:
            if self.watcher:
                self.watcher.stop()
            
            self.running = False
            logger.info("Stopped WebSocket file watcher")
            
        except Exception as e:
            logger.error(f"Error stopping WebSocket file watcher: {e}")
    
    def _on_file_change(self, event_type: str, file_path: str, metadata: dict):
        """
        Handle file change events and broadcast via WebSocket.
        
        Args:
            event_type: Type of change (created, modified, deleted)
            file_path: Path to the changed file
            metadata: Change metadata
        """
        try:
            # Extract entity information
            file_path_obj = Path(file_path)
            entity_data = None
            entity_type = None
            
            # Try to determine entity type from path
            if "revenue" in file_path:
                if "grants" in file_path:
                    entity_type = "grant"
                elif "investments" in file_path:
                    entity_type = "investment"
                elif "sales" in file_path:
                    entity_type = "sale"
                elif "services" in file_path:
                    entity_type = "service"
            elif "expenses" in file_path:
                if "employees" in file_path:
                    entity_type = "employee"
                elif "facilities" in file_path:
                    entity_type = "facility"
                elif "software" in file_path:
                    entity_type = "software"
                elif "equipment" in file_path:
                    entity_type = "equipment"
            elif "projects" in file_path:
                entity_type = "project"
            
            # Try to load entity data for created/modified files
            if event_type in ['created', 'modified'] and self.watcher:
                try:
                    entity = self.watcher.loader.load_entity(file_path_obj)
                    entity_data = entity.model_dump() if hasattr(entity, 'model_dump') else dict(entity)
                except Exception as e:
                    logger.warning(f"Could not load entity data from {file_path}: {e}")
            
            # Broadcast the change
            asyncio.create_task(
                broadcast_entity_change(
                    event_type=event_type,
                    file_path=file_path,
                    entity_data={
                        "entity_type": entity_type,
                        "entity_id": file_path_obj.stem,
                        "data": entity_data,
                        "metadata": metadata
                    }
                )
            )
            
            logger.debug(f"Broadcasted entity change: {event_type} {file_path}")
            
        except Exception as e:
            logger.error(f"Error handling file change for WebSocket broadcast: {e}")
    
    def _on_validation_error(self, file_path: str, error_message: str):
        """
        Handle validation errors and broadcast via WebSocket.
        
        Args:
            file_path: Path to the file with validation errors
            error_message: Error message
        """
        try:
            # Parse error message to extract individual errors
            errors = [error_message]
            if "Validation errors" in error_message:
                # Split multi-line error messages
                errors = error_message.split('\n')[1:]  # Skip the header line
                errors = [err.strip() for err in errors if err.strip()]
            
            # Broadcast the validation error
            asyncio.create_task(
                broadcast_validation_error(
                    file_path=file_path,
                    errors=errors
                )
            )
            
            logger.debug(f"Broadcasted validation error for: {file_path}")
            
        except Exception as e:
            logger.error(f"Error handling validation error for WebSocket broadcast: {e}")
    
    def get_change_log(self, limit: int = 10) -> list:
        """
        Get recent file changes.
        
        Args:
            limit: Maximum number of changes to return
            
        Returns:
            List of recent changes
        """
        if self.watcher:
            return self.watcher.get_change_log(limit)
        return []
    
    async def validate_all_files(self) -> Dict[str, list]:
        """
        Validate all entity files and broadcast results.
        
        Returns:
            Dictionary of file_path -> list of validation errors
        """
        if not self.watcher:
            return {}
        
        try:
            # Run validation in executor to avoid blocking
            loop = asyncio.get_event_loop()
            errors = await loop.run_in_executor(
                None, 
                self.watcher.validate_all_files
            )
            
            # Broadcast validation results
            for file_path, file_errors in errors.items():
                if file_errors:
                    await broadcast_validation_error(file_path, file_errors)
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating all files: {e}")
            return {}


class WebSocketEntityBridge:
    """Bridge between entity operations and WebSocket notifications."""
    
    @staticmethod
    async def notify_entity_created(entity_type: str, entity_id: str, entity_data: dict):
        """
        Notify WebSocket clients of new entity creation.
        
        Args:
            entity_type: Type of entity created
            entity_id: Entity identifier
            entity_data: Entity data
        """
        await broadcast_entity_change(
            event_type="created",
            file_path=f"entities/{entity_type}/{entity_id}.yaml",
            entity_data={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "data": entity_data
            }
        )
    
    @staticmethod
    async def notify_entity_updated(entity_type: str, entity_id: str, entity_data: dict):
        """
        Notify WebSocket clients of entity updates.
        
        Args:
            entity_type: Type of entity updated
            entity_id: Entity identifier
            entity_data: Updated entity data
        """
        await broadcast_entity_change(
            event_type="modified",
            file_path=f"entities/{entity_type}/{entity_id}.yaml",
            entity_data={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "data": entity_data
            }
        )
    
    @staticmethod
    async def notify_entity_deleted(entity_type: str, entity_id: str):
        """
        Notify WebSocket clients of entity deletion.
        
        Args:
            entity_type: Type of entity deleted
            entity_id: Entity identifier
        """
        await broadcast_entity_change(
            event_type="deleted",
            file_path=f"entities/{entity_type}/{entity_id}.yaml",
            entity_data={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "data": None
            }
        )


# Global WebSocket file watcher instance
websocket_file_watcher: Optional[WebSocketFileWatcher] = None


async def start_websocket_file_watcher(entities_dir: str = "entities"):
    """
    Start the global WebSocket file watcher.
    
    Args:
        entities_dir: Directory to watch
    """
    global websocket_file_watcher
    
    if websocket_file_watcher is None:
        websocket_file_watcher = WebSocketFileWatcher(entities_dir)
    
    await websocket_file_watcher.start()


async def stop_websocket_file_watcher():
    """Stop the global WebSocket file watcher."""
    global websocket_file_watcher
    
    if websocket_file_watcher:
        await websocket_file_watcher.stop()


def get_websocket_file_watcher() -> Optional[WebSocketFileWatcher]:
    """Get the global WebSocket file watcher instance."""
    return websocket_file_watcher