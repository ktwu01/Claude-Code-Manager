from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str = ""
    description: str
    project_id: int | None = None
    target_repo: str | None = None
    target_branch: str = "main"
    priority: int = 0
    max_retries: int = 2
    mode: str = "auto"  # "auto" or "plan"
    tags: list[str] | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: int | None = None
    project_id: int | None = None
    target_repo: str | None = None
    target_branch: str | None = None
    max_retries: int | None = None
    mode: str | None = None
    tags: list[str] | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: int
    project_id: int | None
    target_repo: str | None
    target_branch: str
    result_branch: str | None
    merge_status: str
    instance_id: int | None
    retry_count: int
    max_retries: int
    mode: str
    plan_content: str | None
    plan_approved: bool | None
    session_id: str | None
    error_message: str | None
    tags: list[str] | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}
