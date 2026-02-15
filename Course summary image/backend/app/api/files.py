from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.core.config import settings
import os

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/outputs/{filename}", summary="获取生成的文件")
async def get_output_file(filename: str):
    """Serve a generated output file"""
    file_path = os.path.join(settings.OPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type="image/png",
        filename=filename
    )


@router.get("/uploads/{filename}", summary="获取上传的文件")
async def get_uploaded_file(filename: str):
    """Serve an uploaded file"""
    from fastapi import HTTPException

    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf"
    )
