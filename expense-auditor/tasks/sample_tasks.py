"""
Sample Celery tasks with retry logic.
"""
import logging
import time
from typing import Dict, Any, Optional

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger

from tasks.celery_app import celery_app

# Configure logger
logger = get_task_logger(__name__)


class BaseTask(Task):
    """Base task with error handling and retry logic."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 5}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(
            f"Task {self.name}[{task_id}] failed: {exc}",
            exc_info=einfo
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(
            f"Task {self.name}[{task_id}] retrying: {exc}",
            exc_info=einfo
        )
        super().on_retry(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(f"Task {self.name}[{task_id}] completed successfully")
        super().on_success(retval, task_id, args, kwargs)


@celery_app.task(base=BaseTask, name="tasks.process_data")
def process_data(data: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Process data asynchronously.
    
    Args:
        data: The data to process
        options: Optional processing options
    
    Returns:
        Dict containing the processing results
    """
    logger.info(f"Processing data: {data}")
    
    try:
        # Simulate processing time
        time.sleep(2)
        
        # Simulate processing logic
        result = {
            "processed": True,
            "input_size": len(data),
            "timestamp": time.time(),
        }
        
        if options and options.get("raise_error"):
            # For testing error handling
            raise ValueError("Simulated error in task")
        
        return result
    
    except SoftTimeLimitExceeded:
        logger.error("Task exceeded time limit")
        raise
    except Exception as e:
        logger.exception(f"Error processing data: {e}")
        raise


@celery_app.task(base=BaseTask, name="tasks.cleanup")
def cleanup(task_id: str) -> bool:
    """
    Cleanup after task execution.
    
    Args:
        task_id: ID of the task to clean up after
    
    Returns:
        True if cleanup was successful
    """
    logger.info(f"Cleaning up after task {task_id}")
    
    # Simulate cleanup logic
    time.sleep(1)
    
    return True
