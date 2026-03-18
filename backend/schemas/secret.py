from datetime import datetime

from pydantic import BaseModel


class SecretCreate(BaseModel):
    name: str
    content: str


class SecretUpdate(BaseModel):
    name: str | None = None
    content: str | None = None


class SecretResponse(BaseModel):
    id: int
    name: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
