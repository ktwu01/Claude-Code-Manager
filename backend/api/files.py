import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/files", tags=["files"])

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB


def _safe_path(path: str) -> Path:
    """Resolve path and guard against empty input."""
    if not path or not path.strip():
        raise HTTPException(status_code=400, detail="path is required")
    resolved = Path(path).expanduser().resolve()
    return resolved


@router.get("/list")
async def list_directory(path: str = Query(..., description="Absolute directory path")):
    """List contents of a directory."""
    target = _safe_path(path)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    entries = []
    try:
        for entry in sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            try:
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "path": str(entry),
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size if entry.is_file() else None,
                })
            except OSError:
                pass  # skip unreadable entries
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {"path": str(target), "entries": entries}


@router.get("/read")
async def read_file(path: str = Query(..., description="Absolute file path")):
    """Read a file's content (max 1 MB)."""
    target = _safe_path(path)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    if not target.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    size = target.stat().st_size
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size // 1024} KB). Max is {MAX_FILE_SIZE // 1024} KB.",
        )

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {"path": str(target), "content": content, "size": size}
