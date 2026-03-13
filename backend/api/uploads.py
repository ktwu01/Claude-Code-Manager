import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# Project root / uploads
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = _PROJECT_ROOT / "uploads"

_ALLOWED_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
_MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
_MAX_FILES = 5


def _get_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


@router.post("")
async def upload_images(files: list[UploadFile] = File(...)):
    """Upload up to 5 images. Returns list of {id, filename, path, url}."""
    if len(files) > _MAX_FILES:
        raise HTTPException(400, f"Maximum {_MAX_FILES} files allowed per request")

    results = []
    for file in files:
        if file.content_type not in _ALLOWED_TYPES:
            raise HTTPException(
                400,
                f"File type '{file.content_type}' not allowed. Allowed: png, jpg, gif, webp",
            )

        data = await file.read()
        if len(data) > _MAX_SIZE_BYTES:
            raise HTTPException(400, f"File '{file.filename}' exceeds 10 MB limit")

        ext = Path(file.filename or "image").suffix.lower() or ".png"
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{ext}"

        save_path = _get_upload_dir() / filename
        save_path.write_bytes(data)

        results.append(
            {
                "id": file_id,
                "filename": file.filename,
                "path": str(save_path.resolve()),
                "url": f"/api/uploads/{filename}",
            }
        )

    return results


@router.get("/{filename}")
async def get_image(filename: str):
    """Serve an uploaded image (used for frontend preview)."""
    upload_dir = _get_upload_dir()
    file_path = upload_dir / filename

    # Prevent path traversal
    if not str(file_path.resolve()).startswith(str(upload_dir.resolve())):
        raise HTTPException(400, "Invalid filename")
    if not file_path.exists():
        raise HTTPException(404, "File not found")

    return FileResponse(str(file_path))
