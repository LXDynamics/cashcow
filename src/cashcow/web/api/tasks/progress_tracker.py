"""
Progress tracking for background jobs.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    """Job execution result."""
    job_id: str
    status: JobStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: float = 0.0
    progress_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """Get job duration in seconds."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]


class ProgressTracker:
    """Tracks progress for a background job."""
    
    def __init__(self, job_id: str, callback: Optional[Callable] = None):
        """
        Initialize progress tracker.
        
        Args:
            job_id: Unique job identifier
            callback: Optional callback for progress updates
        """
        self.job_id = job_id
        self.callback = callback
        self.result = JobResult(job_id=job_id, status=JobStatus.PENDING)
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Mark job as started."""
        async with self._lock:
            self.result.status = JobStatus.RUNNING
            self.result.started_at = time.time()
            await self._notify_callback()
    
    async def update_progress(self, progress: float, message: str = ""):
        """
        Update job progress.
        
        Args:
            progress: Progress percentage (0.0 to 1.0)
            message: Progress message
        """
        async with self._lock:
            self.result.progress = max(0.0, min(1.0, progress))
            self.result.progress_message = message
            await self._notify_callback()
    
    async def complete(self, result: Any = None):
        """
        Mark job as completed.
        
        Args:
            result: Job result data
        """
        async with self._lock:
            self.result.status = JobStatus.COMPLETED
            self.result.completed_at = time.time()
            self.result.progress = 1.0
            self.result.result = result
            await self._notify_callback()
    
    async def fail(self, error: str):
        """
        Mark job as failed.
        
        Args:
            error: Error message
        """
        async with self._lock:
            self.result.status = JobStatus.FAILED
            self.result.completed_at = time.time()
            self.result.error = error
            await self._notify_callback()
    
    async def cancel(self):
        """Mark job as cancelled."""
        async with self._lock:
            self.result.status = JobStatus.CANCELLED
            self.result.completed_at = time.time()
            await self._notify_callback()
    
    async def set_metadata(self, **metadata):
        """
        Set job metadata.
        
        Args:
            **metadata: Metadata key-value pairs
        """
        async with self._lock:
            self.result.metadata.update(metadata)
            await self._notify_callback()
    
    async def _notify_callback(self):
        """Notify callback of progress update."""
        if self.callback:
            try:
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(self.result)
                else:
                    self.callback(self.result)
            except Exception as e:
                # Don't let callback errors affect the job
                print(f"Error in progress callback: {e}")
    
    def get_result(self) -> JobResult:
        """Get current job result."""
        return self.result
    
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.result.status == JobStatus.RUNNING
    
    def is_completed(self) -> bool:
        """Check if job completed successfully."""
        return self.result.status == JobStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.result.status == JobStatus.FAILED


class JobRegistry:
    """Registry for tracking multiple jobs."""
    
    def __init__(self, max_history: int = 100):
        """
        Initialize job registry.
        
        Args:
            max_history: Maximum number of completed jobs to keep in history
        """
        self.max_history = max_history
        self.active_jobs: Dict[str, ProgressTracker] = {}
        self.completed_jobs: List[JobResult] = []
        self._lock = asyncio.Lock()
    
    async def create_tracker(self, job_id: Optional[str] = None, 
                           callback: Optional[Callable] = None) -> ProgressTracker:
        """
        Create a new progress tracker.
        
        Args:
            job_id: Optional job ID (will generate one if not provided)
            callback: Optional progress callback
            
        Returns:
            New ProgressTracker instance
        """
        if not job_id:
            job_id = str(uuid4())
        
        tracker = ProgressTracker(job_id, callback)
        
        async with self._lock:
            self.active_jobs[job_id] = tracker
        
        return tracker
    
    async def get_tracker(self, job_id: str) -> Optional[ProgressTracker]:
        """
        Get tracker for a job ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            ProgressTracker if found, None otherwise
        """
        return self.active_jobs.get(job_id)
    
    async def get_job_result(self, job_id: str) -> Optional[JobResult]:
        """
        Get job result by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobResult if found, None otherwise
        """
        # Check active jobs first
        tracker = self.active_jobs.get(job_id)
        if tracker:
            return tracker.get_result()
        
        # Check completed jobs
        for result in self.completed_jobs:
            if result.job_id == job_id:
                return result
        
        return None
    
    async def mark_completed(self, job_id: str):
        """
        Move job from active to completed.
        
        Args:
            job_id: Job identifier
        """
        async with self._lock:
            tracker = self.active_jobs.pop(job_id, None)
            if tracker:
                self.completed_jobs.append(tracker.get_result())
                
                # Trim history if needed
                if len(self.completed_jobs) > self.max_history:
                    self.completed_jobs = self.completed_jobs[-self.max_history:]
    
    async def get_active_jobs(self) -> Dict[str, JobResult]:
        """
        Get all active job results.
        
        Returns:
            Dictionary of job_id -> JobResult for active jobs
        """
        results = {}
        for job_id, tracker in self.active_jobs.items():
            results[job_id] = tracker.get_result()
        return results
    
    async def get_completed_jobs(self, limit: int = 10) -> List[JobResult]:
        """
        Get recent completed jobs.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of completed JobResults
        """
        return self.completed_jobs[-limit:]
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was cancelled, False if not found
        """
        tracker = self.active_jobs.get(job_id)
        if tracker and tracker.is_running():
            await tracker.cancel()
            await self.mark_completed(job_id)
            return True
        return False
    
    async def cleanup_completed_jobs(self, max_age_seconds: int = 3600):
        """
        Clean up old completed jobs.
        
        Args:
            max_age_seconds: Maximum age of completed jobs to keep
        """
        if not self.completed_jobs:
            return
        
        cutoff_time = time.time() - max_age_seconds
        
        async with self._lock:
            self.completed_jobs = [
                job for job in self.completed_jobs
                if job.completed_at and job.completed_at > cutoff_time
            ]


# Global job registry instance
job_registry = JobRegistry()