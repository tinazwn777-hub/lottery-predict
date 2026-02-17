from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceType(str, Enum):
    WEB = "web"
    PDF = "pdf"
    FEISHU = "feishu"


class ThemeType(str, Enum):
    LIGHT = "light"
    DARK = "dark"


# Request schemas
class TaskCreateRequest(BaseModel):
    source_type: SourceType
    source_url: Optional[HttpUrl] = None
    source_filename: Optional[str] = None
    gradient_theme: Optional[int] = None  # 1-6 对应6种渐变主题
    config: Optional[Dict[str, Any]] = None


class ImageConfig(BaseModel):
    theme: ThemeType = ThemeType.LIGHT
    gradient_theme: Optional[int] = None  # 1-6 对应6种渐变主题
    title: Optional[str] = None
    font_size: int = 20
    line_height: int = 1.8
    primary_color: str = "#2563eb"
    width: int = 1200  # 横向 A4 比例
    height: int = 800


# Response schemas
class TaskResponse(BaseModel):
    id: str
    source_type: str
    source_url: Optional[str] = None
    source_filename: Optional[str] = None
    status: str
    progress: int
    content: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


class ImageResponse(BaseModel):
    id: str
    task_id: str
    theme: str
    image_url: Optional[str] = None
    local_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

    class Config:
        from_attributes = True


class TaskWithImagesResponse(TaskResponse):
    images: List[ImageResponse] = []


class ContentItem(BaseModel):
    """Single content item for the summary"""
    title: str
    points: List[str]
    order: int = 0


class ParsedContent(BaseModel):
    """Parsed content structure"""
    title: str
    items: List[ContentItem]
    source_url: Optional[str] = None
    source_title: Optional[str] = None


# Web scraping schemas
class WebScrapeRequest(BaseModel):
    url: HttpUrl
    extract_main_content: bool = True


class WebScrapeResponse(BaseModel):
    url: str
    title: str
    content: str
    extracted_content: Optional[ParsedContent] = None


# PDF schemas
class PDFProcessRequest(BaseModel):
    filename: str
    max_pages: int = 100


class PDFProcessResponse(BaseModel):
    filename: str
    page_count: int
    content: str
    extracted_content: Optional[ParsedContent] = None


# Image generation schemas
class ImageGenerateRequest(BaseModel):
    task_id: str
    content: ParsedContent
    config: ImageConfig
    theme: ThemeType


# Upload schemas
class UploadResponse(BaseModel):
    filename: str
    file_path: str
    file_size: int
    content_type: str


# Error schemas
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
