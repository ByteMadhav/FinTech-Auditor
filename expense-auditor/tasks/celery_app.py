import os
import multiprocessing
from celery import Celery
from dotenv import load_dotenv

if __name__ == "__main__" or True:
    multiprocessing.set_start_method("spawn", force=True)

load_dotenv()

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "tasks",
    broker=broker_url,
    backend=result_backend,
    include=[
        "tasks.sample_tasks",
        "tasks.celery_worker"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)