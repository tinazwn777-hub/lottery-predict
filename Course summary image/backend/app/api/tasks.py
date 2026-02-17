from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from app.models.schemas import (
    TaskResponse, TaskWithImagesResponse, TaskCreateRequest,
    WebScrapeRequest, WebScrapeResponse, ImageConfig, ThemeType
)
from app.models.database import Task as TaskModel, TaskStatus, Image as ImageModel
import uuid

router = APIRouter()


def run_pipeline_sync(task_id: str, source_type: str, source: str, filename: str = None, gradient_theme: int = None):
    """同步执行完整处理流程"""
    import asyncio
    from datetime import datetime
    from app.core.database import AsyncSessionLocal
    from app.services.parser.web_parser import WebParser
    from app.services.parser.pdf_parser import PDFParser
    from app.services.image.api_screenshot import ScreenshotAPIService
    from app.core.config import settings
    from app.models.schemas import ParsedContent, ImageConfig as ImageConfigSchema, ThemeType as ThemeTypeEnum
    import os

    async def _process():
        async with AsyncSessionLocal() as session:
            task = await session.get(TaskModel, uuid.UUID(task_id))
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

                # Step 2: Generate images using API screenshot service
                config = ImageConfigSchema(gradient_theme=gradient_theme)
                screenshot_service = ScreenshotAPIService()
                output_dir = settings.OUTPUT_DIR
                os.makedirs(output_dir, exist_ok=True)

                # 生成渐变主题或简洁主题
                if gradient_theme:
                    output_path = os.path.join(output_dir, f"{task_id}_gradient_{gradient_theme}.png")
                    try:
                        screenshot_service.generate(content, config, output_path)
                    except Exception as e:
                        # 如果 API 失败，尝试本地渲染
                        screenshot_service.generate_local(content, config, output_path)

                    image = ImageModel(
                        task_id=task.id,
                        theme=f"gradient_{gradient_theme}",
                        local_path=output_path,
                        width=1200,
                        height=800
                    )
                    session.add(image)
                else:
                    # 默认生成 light 和 dark 两种主题
                    for theme in [ThemeTypeEnum.LIGHT, ThemeTypeEnum.DARK]:
                        output_path = os.path.join(output_dir, f"{task_id}_{theme.value}.png")
                        config.theme = theme
                        try:
                            screenshot_service.generate(content, config, output_path)
                        except Exception as e:
                            screenshot_service.generate_local(content, config, output_path)

                        image = ImageModel(
                            task_id=task.id,
                            theme=theme.value,
                            local_path=output_path,
                            width=1200,
                            height=800
                        )
                        session.add(image)

                task.status = TaskStatus.COMPLETED.value
                task.progress = 100
                task.completed_at = datetime.utcnow()
                await session.commit()

                return {"success": True, "task_id": task_id}

            except Exception as e:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                await session.commit()
                raise

    return asyncio.run(_process())


def regenerate_image_sync(task_id: str, theme: str):
    """同步重新生成图片"""
    import asyncio
    from datetime import datetime
    from app.core.database import AsyncSessionLocal
    from app.services.image.api_screenshot import ScreenshotAPIService
    from app.core.config import settings
    from app.models.schemas import ParsedContent, ImageConfig as ImageConfigSchema, ThemeType as ThemeTypeEnum
    from sqlalchemy import select
    import os

    async def _regenerate():
        async with AsyncSessionLocal() as session:
            task = await session.get(TaskModel, uuid.UUID(task_id))
            if not task:
                return {"error": "Task not found"}

            try:
                task.status = TaskStatus.PROCESSING.value
                task.progress = 90
                await session.commit()

                # Reconstruct content
                content = ParsedContent(**task.content)

                # Determine if gradient theme
                if theme.startswith("gradient_"):
                    gradient_idx = int(theme.split("_")[1])
                    config = ImageConfigSchema(gradient_theme=gradient_idx)
                else:
                    config = ImageConfigSchema(theme=ThemeTypeEnum(theme))

                # Generate image
                screenshot_service = ScreenshotAPIService()
                output_dir = settings.OUTPUT_DIR
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{task_id}_{theme}.png")

                try:
                    screenshot_service.generate(content, config, output_path)
                except Exception as e:
                    screenshot_service.generate_local(content, config, output_path)

                # Update or create image record
                result = await session.execute(
                    select(ImageModel).where(
                        ImageModel.task_id == task.id,
                        ImageModel.theme == theme
                    )
                )
                existing_image = result.scalar_one_or_none()

                if existing_image:
                    existing_image.local_path = output_path
                    existing_image.width = 1200
                    existing_image.height = 800
                    image_id = existing_image.id
                else:
                    image = ImageModel(
                        task_id=task.id,
                        theme=theme,
                        local_path=output_path,
                        width=1200,
                        height=800
                    )
                    session.add(image)
                    image_id = image.id

                task.status = TaskStatus.COMPLETED.value
                task.progress = 100
                task.completed_at = datetime.utcnow()
                await session.commit()

                return {"success": True, "image_id": str(image_id)}

            except Exception as e:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                await session.commit()
                raise

    return asyncio.run(_regenerate())


@router.post("/tasks", response_model=TaskResponse, summary="创建新任务")
async def create_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):
    """Create a new task for parsing content and generating image"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        task = TaskModel(
            source_type=request.source_type.value,
            source_url=str(request.source_url) if request.source_url else None,
            source_filename=request.source_filename,
            status=TaskStatus.PROCESSING.value,
            config=request.config
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

        # Run pipeline synchronously (in background)
        source = str(request.source_url) if request.source_url else request.source_filename
        background_tasks.add_task(
            run_pipeline_sync,
            str(task.id),
            request.source_type.value,
            source,
            request.source_filename,
            request.gradient_theme
        )

        return TaskResponse(**task.to_dict())


@router.get("/tasks/{task_id}", response_model=TaskWithImagesResponse, summary="获取任务详情")
async def get_task(task_id: str):
    """Get task details including generated images"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select

    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TaskModel).where(TaskModel.id == task_uuid)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get images
        result = await session.execute(
            select(ImageModel).where(ImageModel.task_id == task_uuid)
        )
        images = result.scalars().all()

        response = TaskWithImagesResponse(**task.to_dict())
        response.images = [img.to_dict() for img in images]

        return response


@router.get("/tasks/{task_id}/status", summary="获取任务状态")
async def get_task_status(task_id: str):
    """Get only task status and progress"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select

    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TaskModel).where(TaskModel.id == task_uuid)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "task_id": str(task.id),
            "status": task.status,
            "progress": task.progress,
            "error_message": task.error_message,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }


@router.post("/tasks/{task_id}/regenerate/{theme}", response_model=TaskResponse, summary="重新生成图片")
async def regenerate_image(task_id: str, theme: str, background_tasks: BackgroundTasks):
    """Regenerate image with specified theme"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select

    # Validate theme
    valid_themes = [t.value for t in ThemeType] + [f"gradient_{i}" for i in range(1, 7)]
    if theme not in valid_themes:
        raise HTTPException(status_code=400, detail="Invalid theme")

    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TaskModel).where(TaskModel.id == task_uuid)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status != TaskStatus.COMPLETED.value:
            raise HTTPException(status_code=400, detail="Task not completed")

        # Delete existing image for this theme
        result = await session.execute(
            select(ImageModel).where(
                ImageModel.task_id == task_uuid,
                ImageModel.theme == theme
            )
        )
        existing_image = result.scalar_one_or_none()
        if existing_image:
            await session.delete(existing_image)

        # Run regeneration synchronously
        task.status = TaskStatus.PROCESSING.value
        task.progress = 90
        await session.commit()

        background_tasks.add_task(regenerate_image_sync, task_id, theme)

        return TaskResponse(**task.to_dict())


@router.get("/tasks", response_model=list[TaskResponse], summary="获取所有任务")
async def list_tasks(limit: int = 20, offset: int = 0):
    """List all tasks with pagination"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select, desc

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TaskModel)
            .order_by(desc(TaskModel.created_at))
            .offset(offset)
            .limit(limit)
        )
        tasks = result.scalars().all()

        return [TaskResponse(**task.to_dict()) for task in tasks]


@router.delete("/tasks/{task_id}", summary="删除任务")
async def delete_task(task_id: str):
    """Delete a task and its associated images"""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select, delete
    import os

    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    async with AsyncSessionLocal() as session:
        # Get images to delete files
        result = await session.execute(
            select(ImageModel).where(ImageModel.task_id == task_uuid)
        )
        images = result.scalars().all()

        # Delete image files
        for image in images:
            if image.local_path and os.path.exists(image.local_path):
                os.remove(image.local_path)

        # Delete task (cascades to images)
        await session.execute(
            delete(TaskModel).where(TaskModel.id == task_uuid)
        )
        await session.commit()

        return {"message": "Task deleted successfully"}
