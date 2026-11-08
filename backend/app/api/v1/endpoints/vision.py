"""Vision / sketch estimation endpoints."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.lead import VisionEstimateResponseSchema
from app.services.vision_service import VisionService

router = APIRouter(prefix="/vision", tags=["vision"])

MAX_BYTES = 8 * 1024 * 1024

def sniff_image_mime(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if data.startswith(b"RIFF") and b"WEBP" in data[:16]:
        return "image/webp"
    return None


@router.post("/estimate-sketch", response_model=VisionEstimateResponseSchema)
async def estimate_sketch(
    file: UploadFile = File(..., description="Sketch, drawing or photo"),
) -> VisionEstimateResponseSchema:
    """Extract furniture parameters from an uploaded image."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Пустой файл.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Файл больше 8 МБ.")

    sniffed = sniff_image_mime(data)
    if sniffed is None:
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только изображения (JPEG, PNG, WEBP, GIF).",
        )
    content_type = sniffed

    service = VisionService()
    return await service.estimate_sketch(
        file_bytes=data,
        content_type=content_type,
        filename=file.filename or "sketch.jpg",
    )
