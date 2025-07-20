"""
Job manager for handling background tasks.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from .progress_tracker import ProgressTracker, JobRegistry, JobResult, JobStatus


logger = logging.getLogger(__name__)


class JobManager:
    """Manages background job execution and lifecycle."""
    
    def __init__(self, max_concurrent_jobs: int = 5):
        """
        Initialize job manager.
        
        Args:
            max_concurrent_jobs: Maximum number of concurrent jobs
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        self.registry = JobRegistry()
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.worker_tasks: List[asyncio.Task] = []
        self.running = False
        self._progress_callbacks: List[Callable] = []
    
    async def start(self):
        """Start the job manager and worker tasks."""
        if self.running:
            return
        
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent_jobs):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        logger.info(f"Started job manager with {self.max_concurrent_jobs} workers")
    
    async def stop(self):
        """Stop the job manager and cancel all tasks."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        logger.info("Stopped job manager")
    
    async def submit_job(self, 
                        job_func: Callable,
                        job_args: tuple = (),
                        job_kwargs: dict = None,
                        job_id: Optional[str] = None,
                        priority: int = 0,
                        metadata: Dict[str, Any] = None) -> str:
        """
        Submit a job for background execution.
        
        Args:
            job_func: Function to execute
            job_args: Positional arguments for the function
            job_kwargs: Keyword arguments for the function
            job_id: Optional job ID (will generate if not provided)
            priority: Job priority (higher = more important)
            metadata: Optional job metadata
            
        Returns:
            Job ID
        """
        if not job_id:
            job_id = str(uuid4())
        
        if job_kwargs is None:
            job_kwargs = {}
        
        if metadata is None:
            metadata = {}
        
        # Create progress tracker
        tracker = await self.registry.create_tracker(
            job_id=job_id,
            callback=self._on_progress_update
        )
        
        # Set initial metadata
        await tracker.set_metadata(**metadata)
        
        # Create job item
        job_item = {
            "job_id": job_id,
            "job_func": job_func,
            "job_args": job_args,
            "job_kwargs": job_kwargs,
            "priority": priority,
            "tracker": tracker
        }
        
        # Add to queue
        await self.job_queue.put(job_item)
        
        logger.info(f"Submitted job {job_id} to queue")
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[JobResult]:
        """
        Get status of a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobResult if found, None otherwise
        """
        return await self.registry.get_job_result(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was cancelled, False if not found or already completed
        """
        return await self.registry.cancel_job(job_id)
    
    async def get_active_jobs(self) -> Dict[str, JobResult]:
        """Get all active jobs."""
        return await self.registry.get_active_jobs()
    
    async def get_completed_jobs(self, limit: int = 10) -> List[JobResult]:
        """Get recent completed jobs."""
        return await self.registry.get_completed_jobs(limit)
    
    def add_progress_callback(self, callback: Callable[[JobResult], None]):
        """
        Add a callback for job progress updates.
        
        Args:
            callback: Function to call on progress updates
        """
        self._progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[JobResult], None]):
        """
        Remove a progress callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)
    
    async def _worker(self, worker_name: str):
        """
        Worker task that processes jobs from the queue.
        
        Args:
            worker_name: Name of the worker for logging
        """
        logger.info(f"Started worker: {worker_name}")
        
        while self.running:
            try:
                # Get job from queue with timeout
                job_item = await asyncio.wait_for(
                    self.job_queue.get(),
                    timeout=1.0
                )
                
                await self._execute_job(job_item, worker_name)
                
            except asyncio.TimeoutError:
                # Timeout is normal, just continue
                continue
            except asyncio.CancelledError:
                # Worker is being cancelled
                break
            except Exception as e:
                logger.error(f"Error in worker {worker_name}: {e}")
        
        logger.info(f"Stopped worker: {worker_name}")
    
    async def _execute_job(self, job_item: dict, worker_name: str):
        """
        Execute a single job.
        
        Args:
            job_item: Job information dictionary
            worker_name: Name of the executing worker
        """
        job_id = job_item["job_id"]
        job_func = job_item["job_func"]
        job_args = job_item["job_args"]
        job_kwargs = job_item["job_kwargs"]
        tracker = job_item["tracker"]
        
        logger.info(f"Worker {worker_name} executing job {job_id}")
        
        try:
            # Start the job
            await tracker.start()
            
            # Execute the function
            if asyncio.iscoroutinefunction(job_func):
                # Pass tracker to async functions
                result = await job_func(*job_args, tracker=tracker, **job_kwargs)
            else:
                # Run sync functions in executor
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: job_func(*job_args, **job_kwargs)
                )
            
            # Mark as completed
            await tracker.complete(result)
            logger.info(f"Job {job_id} completed successfully")
            
        except asyncio.CancelledError:
            await tracker.cancel()
            logger.info(f"Job {job_id} was cancelled")
            
        except Exception as e:
            await tracker.fail(str(e))
            logger.error(f"Job {job_id} failed: {e}")
        
        finally:
            # Move to completed jobs
            await self.registry.mark_completed(job_id)
    
    async def _on_progress_update(self, result: JobResult):
        """
        Handle progress updates from jobs.
        
        Args:
            result: Updated job result
        """
        # Call all registered callbacks
        for callback in self._progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result)
                else:
                    callback(result)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")


# Global job manager instance
job_manager = JobManager()