from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    git_url: str
    default_branch: str = "main"


class ProjectUpdate(BaseModel):
    name: str | None = None
    git_url: str | None = None
    default_branch: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    git_url: str
    local_path: str | None
    default_branch: str
    status: str
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
