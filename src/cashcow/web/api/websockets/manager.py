"""
WebSocket connection manager for CashCow real-time updates.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Set
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""
    connection_id: str
    client_ip: str
    connected_at: float
    last_heartbeat: float
    subscriptions: Set[str] = set()
    user_id: Optional[str] = None


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""
    type: str
    data: dict
    timestamp: float = None
    
    def __init__(self, **data):
        if not data.get('timestamp'):
            data['timestamp'] = time.time()
        super().__init__(**data)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of connection_ids
        self.heartbeat_interval = 30.0  # seconds
        self.heartbeat_task: Optional[asyncio.Task] = None
        
    async def connect(self, websocket: WebSocket, client_ip: str, 
                     user_id: Optional[str] = None) -> str:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            client_ip: Client IP address
            user_id: Optional authenticated user ID
            
        Returns:
            Connection ID
        """
        await websocket.accept()
        
        connection_id = str(uuid4())
        current_time = time.time()
        
        # Store connection
        self.active_connections[connection_id] = websocket
        self.connection_info[connection_id] = ConnectionInfo(
            connection_id=connection_id,
            client_ip=client_ip,
            connected_at=current_time,
            last_heartbeat=current_time,
            user_id=user_id
        )
        
        logger.info(f"WebSocket connected: {connection_id} from {client_ip}")
        
        # Start heartbeat task if this is the first connection
        if len(self.active_connections) == 1 and not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect and clean up a WebSocket connection.
        
        Args:
            connection_id: Connection ID to disconnect
        """
        if connection_id in self.active_connections:
            # Remove from all subscriptions
            for topic, subscribers in self.subscriptions.items():
                subscribers.discard(connection_id)
            
            # Clean up connection info
            connection_info = self.connection_info.get(connection_id)
            if connection_info:
                logger.info(f"WebSocket disconnected: {connection_id} from {connection_info.client_ip}")
            
            # Remove connection
            del self.active_connections[connection_id]
            del self.connection_info[connection_id]
            
            # Stop heartbeat task if no connections remain
            if not self.active_connections and self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None
    
    async def send_message(self, connection_id: str, message: WebSocketMessage):
        """
        Send a message to a specific connection.
        
        Args:
            connection_id: Target connection ID
            message: Message to send
        """
        websocket = self.active_connections.get(connection_id)
        if websocket:
            try:
                await websocket.send_text(message.model_dump_json())
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                await self.disconnect(connection_id)
    
    async def broadcast(self, message: WebSocketMessage, topic: Optional[str] = None):
        """
        Broadcast a message to all connections or subscribers of a topic.
        
        Args:
            message: Message to broadcast
            topic: Optional topic to broadcast to (if None, broadcasts to all)
        """
        if topic and topic in self.subscriptions:
            # Broadcast to subscribers of specific topic
            subscribers = self.subscriptions[topic].copy()
            for connection_id in subscribers:
                await self.send_message(connection_id, message)
        else:
            # Broadcast to all connections
            connection_ids = list(self.active_connections.keys())
            for connection_id in connection_ids:
                await self.send_message(connection_id, message)
    
    async def subscribe(self, connection_id: str, topic: str):
        """
        Subscribe a connection to a topic.
        
        Args:
            connection_id: Connection ID
            topic: Topic to subscribe to
        """
        if connection_id not in self.active_connections:
            return
        
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        
        self.subscriptions[topic].add(connection_id)
        
        # Update connection info
        if connection_id in self.connection_info:
            self.connection_info[connection_id].subscriptions.add(topic)
        
        logger.debug(f"Connection {connection_id} subscribed to {topic}")
    
    async def unsubscribe(self, connection_id: str, topic: str):
        """
        Unsubscribe a connection from a topic.
        
        Args:
            connection_id: Connection ID
            topic: Topic to unsubscribe from
        """
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)
            
            # Clean up empty topics
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        
        # Update connection info
        if connection_id in self.connection_info:
            self.connection_info[connection_id].subscriptions.discard(topic)
        
        logger.debug(f"Connection {connection_id} unsubscribed from {topic}")
    
    async def handle_heartbeat(self, connection_id: str):
        """
        Handle heartbeat from a connection.
        
        Args:
            connection_id: Connection ID that sent heartbeat
        """
        if connection_id in self.connection_info:
            self.connection_info[connection_id].last_heartbeat = time.time()
    
    async def _heartbeat_loop(self):
        """Background task to send heartbeats and check for stale connections."""
        while self.active_connections:
            try:
                current_time = time.time()
                stale_connections = []
                
                # Check for stale connections and send heartbeats
                for connection_id, info in self.connection_info.items():
                    if current_time - info.last_heartbeat > self.heartbeat_interval * 2:
                        # Connection is stale
                        stale_connections.append(connection_id)
                    else:
                        # Send heartbeat
                        heartbeat = WebSocketMessage(
                            type="heartbeat",
                            data={"timestamp": current_time}
                        )
                        await self.send_message(connection_id, heartbeat)
                
                # Clean up stale connections
                for connection_id in stale_connections:
                    logger.warning(f"Disconnecting stale connection: {connection_id}")
                    await self.disconnect(connection_id)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    def get_connection_stats(self) -> dict:
        """
        Get statistics about current connections.
        
        Returns:
            Dictionary with connection statistics
        """
        current_time = time.time()
        stats = {
            "total_connections": len(self.active_connections),
            "total_subscriptions": sum(len(subs) for subs in self.subscriptions.values()),
            "topics": list(self.subscriptions.keys()),
            "connections": []
        }
        
        for connection_id, info in self.connection_info.items():
            connection_stats = {
                "connection_id": connection_id,
                "client_ip": info.client_ip,
                "connected_duration": current_time - info.connected_at,
                "last_heartbeat_ago": current_time - info.last_heartbeat,
                "subscriptions": list(info.subscriptions),
                "user_id": info.user_id
            }
            stats["connections"].append(connection_stats)
        
        return stats
    
    async def handle_message(self, connection_id: str, message: dict):
        """
        Handle incoming message from a WebSocket connection.
        
        Args:
            connection_id: Connection ID that sent the message
            message: Parsed message dictionary
        """
        message_type = message.get("type")
        
        if message_type == "heartbeat":
            await self.handle_heartbeat(connection_id)
            
        elif message_type == "subscribe":
            topic = message.get("data", {}).get("topic")
            if topic:
                await self.subscribe(connection_id, topic)
                
        elif message_type == "unsubscribe":
            topic = message.get("data", {}).get("topic")
            if topic:
                await self.unsubscribe(connection_id, topic)
                
        else:
            logger.warning(f"Unknown message type from {connection_id}: {message_type}")


# Global connection manager instance
connection_manager = ConnectionManager()