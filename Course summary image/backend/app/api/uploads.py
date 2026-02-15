from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import os
import uuid
from pathlib import Path
from app.models.schemas import UploadResponse
from app.core.config import settings

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("/file", response_model=UploadResponse, summary="上传文件")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file (PDF, etc.) for processing"""
    # Validate file type
    allowed_types = ["application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    # Validate file size
    file_size = 0
    chunks = 0
    max_size = settings.MAX_FILE_SIZE

    async def file_generator():
        nonlocal file_size, chunks
        async for chunk in file:
            chunks += 1
            file_size += len(chunk)
            if file_size > max_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum allowed ({max_size // (1024*1024)}MB)"
                )
            yield chunk

    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower() if file.filename else ".pdf"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename

    try:
        # Write file
        with open(file_path, "wb") as f:
            async for chunk in file_generator():
                f.write(chunk)

        return UploadResponse(
            filename=unique_filename,
            file_path=str(file_path),
            file_size=file_size,
            content_type=file.content_type
        )

    except HTTPException:
        # Clean up partial file
        if file_path.exists():
            file_path.unlink()
        raise
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.delete("/file/{filename}", summary="删除上传的文件")
async def delete_uploaded_file(filename: str):
    """Delete an uploaded file"""
    file_path = Path(settings.UPLOAD_DIR) / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_path.unlink()
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
