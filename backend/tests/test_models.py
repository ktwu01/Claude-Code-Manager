"""Tests for ORM models — schema correctness and defaults."""
import pytest
import pytest_asyncio

from backend.models.task import Task
from backend.models.instance import Instance
from backend.models.project import Project


@pytest.mark.asyncio
async def test_task_defaults(db_session):
    task = Task(title="t", description="d")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.status == "pending"
    assert task.priority == 0
    assert task.retry_count == 0
    assert task.max_retries == 2
    assert task.mode == "auto"
    assert task.merge_status == "pending"
    assert task.project_id is None
    assert task.target_repo is not None  # defaults to ""


@pytest.mark.asyncio
async def test_task_with_project_id(db_session):
    task = Task(title="t", description="d", project_id=42)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    assert task.project_id == 42


@pytest.mark.asyncio
async def test_instance_defaults(db_session):
    inst = Instance(name="worker-1")
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    assert inst.status == "idle"
    assert inst.model == "sonnet"
    assert inst.total_tasks_completed == 0
    assert inst.total_cost_usd == 0.0
    assert inst.pid is None


@pytest.mark.asyncio
async def test_project_defaults(db_session):
    proj = Project(name="my-project", git_url="https://github.com/user/repo.git")
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)

    assert proj.default_branch == "main"
    assert proj.status == "pending"
    assert proj.local_path is None
    assert proj.error_message is None


@pytest.mark.asyncio
async def test_project_unique_name(db_session):
    from sqlalchemy.exc import IntegrityError

    proj1 = Project(name="same-name", git_url="https://a.git")
    db_session.add(proj1)
    await db_session.commit()

    proj2 = Project(name="same-name", git_url="https://b.git")
    db_session.add(proj2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
