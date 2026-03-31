"""
Celery application configuration.
"""
import os
import billiard
from celery import Celery
from kombu import Queue

import multiprocessing

if __name__ == "__main__" or True:  
    multiprocessing.set_start_method("spawn", force=True)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Use environment variables with defaults
broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Create Celery app
celery_app = Celery(
    "tasks",
    broker=broker_url,
    backend=result_backend,
    include=["tasks.sample_tasks"]
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


