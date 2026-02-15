import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum, UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class TaskStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceType(enum.Enum):
    WEB = "web"
    PDF = "pdf"
    FEISHU = "feishu"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String(20), nullable=False)
    source_url = Column(String(2048), nullable=True)
    source_filename = Column(String(500), nullable=True)
    status = Column(String(20), default=TaskStatus.PENDING.value)
    progress = Column(Integer, default=0)
    content = Column(JSON, nullable=True)
    config = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    images = relationship("Image", back_populates="task", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "source_type": self.source_type,
            "source_url": self.source_url,
            "source_filename": self.source_filename,
            "status": self.status,
            "progress": self.progress,
            "content": self.content,
            "config": self.config,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class Image(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    theme = Column(String(50), nullable=False)
    image_url = Column(String(2048), nullable=True)
    local_path = Column(String(1024), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="images")

    def to_dict(self):
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "theme": self.theme,
            "image_url": self.image_url,
            "local_path": self.local_path,
            "width": self.width,
            "height": self.height,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
