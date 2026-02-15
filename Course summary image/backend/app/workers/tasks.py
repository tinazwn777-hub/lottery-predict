import os
import uuid
from datetime import datetime
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.database import Task, TaskStatus, Image
from app.services.parser.web_parser import WebParser
from app.services.parser.pdf_parser import PDFParser
from app.services.image.generator import ImageGenerator
from app.models.schemas import ImageConfig, ThemeType


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def parse_web_task(self, task_id: str, url: str):
    """Celery task to parse web content"""
    async def _parse():
        async with AsyncSessionLocal() as session:
            # Get task
            task = await session.get(Task, uuid.UUID(task_id))
            if not task:
                return {"error": "Task not found"}

            try:
                # Update status
                task.status = TaskStatus.PROCESSING.value
                task.progress = 10
                await session.commit()

                # Parse web content
                parser = WebParser()
                content = await parser.parse(url)

                # Save content
                task.content = content.model_dump()
                task.progress = 80
                await session.commit()

                return {"success": True, "content": content.model_dump()}

            except Exception as e:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                await session.commit()
                raise

    result = asyncio.run(_parse())
    return result


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def parse_pdf_task(self, task_id: str, file_path: str, filename: str):
    """Celery task to parse PDF content"""
    async def _parse():
        async with AsyncSessionLocal() as session:
            task = await session.get(Task, uuid.UUID(task_id))
            if not task:
                return {"error": "Task not found"}

            try:
                task.status = TaskStatus.PROCESSING.value
                task.progress = 10
                await session.commit()

                # Parse PDF
                parser = PDFParser()
                content = await parser.parse(file_path, filename)

                task.content = content.model_dump()
                task.progress = 80
                await session.commit()

                return {"success": True, "content": content.model_dump()}

            except Exception as e:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                await session.commit()
                raise

    result = asyncio.run(_parse())
    return result


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_image_task(self, task_id: str, theme: str):
    """Celery task to generate summary image"""
    from app.core.config import settings

    async def _generate():
        async with AsyncSessionLocal() as session:
            task = await session.get(Task, uuid.UUID(task_id))
            if not task:
                return {"error": "Task not found"}

            try:
                task.status = TaskStatus.PROCESSING.value
                task.progress = 90
                await session.commit()

                # Import here to avoid circular import
                from app.models.schemas import ParsedContent

                # Reconstruct content
                content = ParsedContent(**task.content)

                # Generate image
                config = ImageConfig(theme=ThemeType(theme))
                generator = ImageGenerator()

                # Output path
                output_dir = settings.OUTPUT_DIR
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{task_id}_{theme}.png")

                generator.generate(content, config, output_path)

                # Create image record
                image = Image(
                    task_id=task.id,
                    theme=theme,
                    local_path=output_path,
                    width=config.width,
                    height=config.height
                )
                session.add(image)

                # Update task
                task.status = TaskStatus.COMPLETED.value
                task.progress = 100
                task.completed_at = datetime.utcnow()
                await session.commit()

                return {
                    "success": True,
                    "image_path": output_path,
                    "image_id": str(image.id)
                }

            except Exception as e:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                await session.commit()
                raise

    result = asyncio.run(_generate())
    return result


@shared_task(bind=True)
def process_full_pipeline(self, task_id: str, source_type: str, source: str, filename: str = None):
    """Full pipeline: parse -> generate image"""
    from app.models.schemas import ParsedContent

    async def _process():
        async with AsyncSessionLocal() as session:
            task = await session.get(Task, uuid.UUID(task_id))
            if not task:
                return {"error": "Task not found"}

            try:
                # Step 1: Parse content
                task.status = TaskStatus.PROCESSING.value
                task.progress = 20
                await session.commit()

                if source_type == "web":
                    parser = WebParser()
                    content = await parser.parse(source)
                elif source_type == "pdf":
                    parser = PDFParser()
                    content = await parser.parse(source, filename or "document.pdf")
                else:
                    raise ValueError(f"Unknown source type: {source_type}")

                task.content = content.model_dump()
                task.progress = 50
                await session.commit()

                # Step 2: Generate images for both themes
                config = ImageConfig()
                generator = ImageGenerator()
                output_dir = settings.OUTPUT_DIR
                os.makedirs(output_dir, exist_ok=True)

                images = []
                for theme in [ThemeType.LIGHT, ThemeType.DARK]:
                    output_path = os.path.join(output_dir, f"{task_id}_{theme.value}.png")
                    generator.generate(content, config, output_path)

                    image = Image(
                        task_id=task.id,
                        theme=theme.value,
                        local_path=output_path,
                        width=config.width,
                        height=config.height
                    )
                    session.add(image)
                    images.append(str(image.id))

                task.status = TaskStatus.COMPLETED.value
                task.progress = 100
                task.completed_at = datetime.utcnow()
                await session.commit()

                return {
                    "success": True,
                    "task_id": task_id,
                    "images": images
                }

            except Exception as e:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                await session.commit()
                raise

    result = asyncio.run(_process())
    return result
