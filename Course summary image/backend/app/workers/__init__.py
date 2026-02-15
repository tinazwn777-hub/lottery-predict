from app.workers.celery_app import celery_app
from app.workers.tasks import (
    parse_web_task,
    parse_pdf_task,
    generate_image_task,
    process_full_pipeline
)
