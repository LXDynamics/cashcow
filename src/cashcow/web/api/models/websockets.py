"""
Pydantic models for WebSocket messages and job processing.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class MessageType(str, Enum):
    """WebSocket message types."""
    # Connection management
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    
    # Subscription management
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SUBSCRIPTION_CONFIRMED = "subscription_confirmed"
    
    # Entity updates
    ENTITY_CHANGE = "entity_change"
    VALIDATION_ERROR = "validation_error"
    ENTITY_LIST_UPDATE = "entity_list_update"
    
    # Calculation updates
    CALCULATION_PROGRESS = "calculation_progress"
    CALCULATION_COMPLETE = "calculation_complete"
    CALCULATION_FAILED = "calculation_failed"
    
    # System status
    STATUS_UPDATE = "status_update"
    SYSTEM_ALERT = "system_alert"
    
    # Job management
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"


class WebSocketBaseMessage(BaseModel):
    """Base WebSocket message structure."""
    type: MessageType
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    data: Dict[str, Any] = Field(default_factory=dict)


class ConnectionRequest(BaseModel):
    """Request to establish WebSocket connection."""
    type: MessageType = MessageType.CONNECTED
    user_id: Optional[str] = None
    client_info: Optional[Dict[str, str]] = None


class SubscriptionRequest(BaseModel):
    """Request to subscribe to a topic."""
    type: MessageType = MessageType.SUBSCRIBE
    topic: str = Field(..., description="Topic to subscribe to")
    
    @validator('topic')
    def validate_topic(cls, v):
        valid_topics = ['calculations', 'entities', 'status', 'jobs']
        if v not in valid_topics:
            raise ValueError(f"Topic must be one of: {valid_topics}")
        return v


class HeartbeatMessage(BaseModel):
    """Heartbeat message."""
    type: MessageType = MessageType.HEARTBEAT
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class ErrorMessage(BaseModel):
    """Error message."""
    type: MessageType = MessageType.ERROR
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None


# Entity-related messages

class EntityChangeMessage(BaseModel):
    """Entity file change notification."""
    type: MessageType = MessageType.ENTITY_CHANGE
    event_type: str = Field(..., description="created, modified, or deleted")
    file_path: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_data: Optional[Dict[str, Any]] = None


class ValidationErrorMessage(BaseModel):
    """Entity validation error notification."""
    type: MessageType = MessageType.VALIDATION_ERROR
    file_path: str
    errors: List[str]
    warnings: Optional[List[str]] = None


# Job-related messages

class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobRequest(BaseModel):
    """Request to start a background job."""
    job_type: str = Field(..., description="Type of job to run")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, description="Job priority")
    metadata: Optional[Dict[str, Any]] = None


class JobProgressMessage(BaseModel):
    """Job progress update message."""
    type: MessageType = MessageType.JOB_PROGRESS
    job_id: str
    job_type: str
    status: JobStatus
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress from 0.0 to 1.0")
    progress_message: str = ""
    metadata: Optional[Dict[str, Any]] = None


class JobResultMessage(BaseModel):
    """Job completion result message."""
    type: MessageType = MessageType.JOB_COMPLETED
    job_id: str
    job_type: str
    status: JobStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


# Calculation-related messages

class CalculationProgressMessage(BaseModel):
    """Calculation progress update."""
    type: MessageType = MessageType.CALCULATION_PROGRESS
    calculation_type: str = Field(..., description="Type of calculation")
    job_id: Optional[str] = None
    progress: float = Field(..., ge=0.0, le=1.0)
    stage: str = ""
    estimated_completion: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class CalculationCompleteMessage(BaseModel):
    """Calculation completion notification."""
    type: MessageType = MessageType.CALCULATION_COMPLETE
    calculation_type: str
    job_id: Optional[str] = None
    duration: float
    result_summary: Dict[str, Any]
    success: bool = True


# System status messages

class SystemStatus(str, Enum):
    """System status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class StatusUpdateMessage(BaseModel):
    """System status update."""
    type: MessageType = MessageType.STATUS_UPDATE
    system_status: SystemStatus
    active_connections: int = 0
    active_jobs: int = 0
    memory_usage: Optional[Dict[str, Union[int, float]]] = None
    uptime: Optional[float] = None
    version: Optional[str] = None


class SystemAlertMessage(BaseModel):
    """System alert notification."""
    type: MessageType = MessageType.SYSTEM_ALERT
    level: SystemStatus
    alert_id: str
    message: str
    source: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    action_required: bool = False


# Response models for REST API

class ConnectionInfo(BaseModel):
    """WebSocket connection information."""
    connection_id: str
    client_ip: str
    connected_at: datetime
    last_heartbeat: datetime
    subscriptions: List[str] = []
    user_id: Optional[str] = None


class ConnectionStats(BaseModel):
    """WebSocket connection statistics."""
    total_connections: int
    total_subscriptions: int
    topics: List[str]
    connections: List[ConnectionInfo]


class JobInfo(BaseModel):
    """Background job information."""
    job_id: str
    job_type: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    progress_message: str = ""
    priority: int = 0
    metadata: Optional[Dict[str, Any]] = None


class JobListResponse(BaseModel):
    """Response for job list queries."""
    active_jobs: List[JobInfo]
    completed_jobs: List[JobInfo]
    total_active: int
    total_completed: int


# WebSocket message union type for message parsing
WebSocketMessage = Union[
    WebSocketBaseMessage,
    ConnectionRequest,
    SubscriptionRequest,
    HeartbeatMessage,
    ErrorMessage,
    EntityChangeMessage,
    ValidationErrorMessage,
    JobProgressMessage,
    JobResultMessage,
    CalculationProgressMessage,
    CalculationCompleteMessage,
    StatusUpdateMessage,
    SystemAlertMessage
]