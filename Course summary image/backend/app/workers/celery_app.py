"""
Celery application configuration
"""

from celery import Celery

# Create Celery app with in-memory backend for development/testing
# Using "rpc://" for result backend (no Redis needed)
celery_app = Celery(
    "app",
    broker="pyamqp://",  # Use RabbitMQ or fall back to in-memory
    backend="cache"
)

# Configure Celery to use local memory cache
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_extended=True,
    # Use local cache for results
    cache_backend="memory",
    result_backend="cache",
    # Don't wait for results synchronously
    task_ignore_result=True,
)
