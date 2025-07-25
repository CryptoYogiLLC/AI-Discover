"""
Celery configuration and initialization
"""

from celery import Celery
from .config import settings

# Create Celery instance
celery_app = Celery(
    "ai_discover",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],  # Include task modules
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configure beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Add periodic tasks here
    # Example:
    # 'sync-resources': {
    #     'task': 'app.tasks.sync_resources',
    #     'schedule': 300.0,  # Run every 5 minutes
    # },
}
