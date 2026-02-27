from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    token: str


@router.post("/login")
async def login(body: LoginRequest):
    """Validate token. Returns ok if token matches."""
    if not settings.auth_token:
        return {"ok": True, "message": "No auth configured"}
    if body.token == settings.auth_token:
        return {"ok": True}
    raise HTTPException(401, "Invalid token")
