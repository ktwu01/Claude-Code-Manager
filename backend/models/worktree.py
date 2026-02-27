from datetime import datetime

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Worktree(Base):
    __tablename__ = "worktrees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_path: Mapped[str] = mapped_column(String(500), nullable=False)
    worktree_path: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    branch_name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(100), default="main")
    instance_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
