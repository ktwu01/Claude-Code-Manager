import asyncio
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db, async_session
from backend.models.project import Project
from backend.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.name))
    return list(result.scalars().all())


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    # Check duplicate name
    existing = await db.execute(select(Project).where(Project.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Project '{body.name}' already exists")

    workspace = os.path.expanduser(settings.workspace_dir)
    local_path = os.path.join(workspace, body.name)

    project = Project(
        name=body.name,
        git_url=body.git_url,
        default_branch=body.default_branch,
        local_path=local_path,
        status="pending",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Clone in background
    asyncio.create_task(_clone_repo(project.id, body.git_url, local_path))

    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int, body: ProjectUpdate, db: AsyncSession = Depends(get_db)
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    await db.delete(project)
    await db.commit()
    return {"ok": True}


@router.post("/{project_id}/reclone")
async def reclone_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project.status = "pending"
    project.error_message = None
    await db.commit()
    asyncio.create_task(_clone_repo(project_id, project.git_url, project.local_path))
    return {"ok": True}


async def _clone_repo(project_id: int, git_url: str, local_path: str):
    """Clone a git repo in the background."""
    async with async_session() as db:
        await db.execute(
            update(Project).where(Project.id == project_id).values(status="cloning")
        )
        await db.commit()

    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        if os.path.isdir(local_path):
            # Already exists, just fetch
            proc = await asyncio.create_subprocess_exec(
                "git", "fetch", "--all",
                cwd=local_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"git fetch failed: {stderr.decode()}")
        else:
            proc = await asyncio.create_subprocess_exec(
                "git", "clone", git_url, local_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"git clone failed: {stderr.decode()}")

        async with async_session() as db:
            await db.execute(
                update(Project).where(Project.id == project_id).values(status="ready")
            )
            await db.commit()

    except Exception as e:
        async with async_session() as db:
            await db.execute(
                update(Project)
                .where(Project.id == project_id)
                .values(status="error", error_message=str(e)[:1000])
            )
            await db.commit()
