from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str
    color: str = "indigo"


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


from datetime import datetime as dt


class TagResponse(BaseModel):
    id: int
    name: str
    color: str
    created_at: dt

    model_config = {"from_attributes": True}
