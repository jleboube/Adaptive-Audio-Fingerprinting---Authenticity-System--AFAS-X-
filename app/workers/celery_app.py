"""Celery application configuration."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "afas_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit at 9 minutes
    worker_prefetch_multiplier=1,  # One task at a time for memory management
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-verification-logs": {
        "task": "app.workers.tasks.cleanup_old_logs",
        "schedule": 86400.0,  # Daily
    },
    "verify-blockchain-integrity": {
        "task": "app.workers.tasks.verify_blockchain",
        "schedule": 3600.0,  # Hourly
    },
}
