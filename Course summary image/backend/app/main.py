from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import init_db
from app.api import tasks, uploads, files


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Create necessary directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    # Initialize database
    init_db()

    yield

    # Shutdown (if needed)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="课程总结图片生成器 - 自动从网页和PDF提取内容并生成美观的总结图片",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")


@app.get("/", summary="API根目录")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health", summary="健康检查")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
