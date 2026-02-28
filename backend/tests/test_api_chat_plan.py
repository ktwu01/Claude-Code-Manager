"""Tests for Chat and Plan API endpoints."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from backend.database import Base, get_db
from backend.models.task import Task


@pytest_asyncio.fixture
async def app(db_engine):
    """Create a test FastAPI app with in-memory DB."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    from backend.main import app as real_app

    async def override_get_db():
        async with session_factory() as session:
            yield session

    real_app.dependency_overrides[get_db] = override_get_db

    from backend.config import settings
    original_token = settings.auth_token
    settings.auth_token = ""

    yield real_app, session_factory

    real_app.dependency_overrides.clear()
    settings.auth_token = original_token


@pytest_asyncio.fixture
async def client(app):
    real_app, _ = app
    transport = ASGITransport(app=real_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def session_factory(app):
    _, factory = app
    return factory


# === Chat tests ===


@pytest.mark.asyncio
async def test_chat_history_not_found(client):
    resp = await client.get("/api/tasks/9999/chat/history")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_history_empty(client):
    create_resp = await client.post("/api/tasks", json={
        "title": "T", "description": "d", "target_repo": "/tmp",
    })
    task_id = create_resp.json()["id"]
    resp = await client.get(f"/api/tasks/{task_id}/chat/history")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_chat_history_returns_tool_fields(client, session_factory):
    """Chat history should include tool_input and tool_output fields."""
    # Create a task
    create_resp = await client.post("/api/tasks", json={
        "title": "T", "description": "d", "target_repo": "/tmp",
    })
    task_id = create_resp.json()["id"]

    # Insert log entries with tool_input/tool_output directly in DB
    from backend.models.log_entry import LogEntry
    async with session_factory() as db:
        # tool_use entry
        db.add(LogEntry(
            instance_id=1,
            task_id=task_id,
            event_type="tool_use",
            role="assistant",
            tool_name="Edit",
            tool_input='{"file_path": "/tmp/test.py", "old_string": "foo", "new_string": "bar"}',
            is_error=False,
        ))
        # tool_result entry
        db.add(LogEntry(
            instance_id=1,
            task_id=task_id,
            event_type="tool_result",
            role="assistant",
            tool_name="Edit",
            tool_output="File updated successfully",
            is_error=False,
        ))
        await db.commit()

    resp = await client.get(f"/api/tasks/{task_id}/chat/history")
    assert resp.status_code == 200
    msgs = resp.json()
    assert len(msgs) == 2

    # tool_use should have tool_input
    assert msgs[0]["event_type"] == "tool_use"
    assert msgs[0]["tool_name"] == "Edit"
    assert msgs[0]["tool_input"] is not None
    assert "file_path" in msgs[0]["tool_input"]

    # tool_result should have tool_output
    assert msgs[1]["event_type"] == "tool_result"
    assert msgs[1]["tool_output"] == "File updated successfully"


@pytest.mark.asyncio
async def test_chat_send_no_session(client):
    """Sending chat to a task with no session should return 400."""
    create_resp = await client.post("/api/tasks", json={
        "title": "T", "description": "d", "target_repo": "/tmp",
    })
    task_id = create_resp.json()["id"]
    resp = await client.post(f"/api/tasks/{task_id}/chat", json={"message": "hello"})
    assert resp.status_code == 400
    assert "session" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_chat_send_task_not_found(client):
    resp = await client.post("/api/tasks/9999/chat", json={"message": "hello"})
    assert resp.status_code == 404


# === Plan tests ===


@pytest.mark.asyncio
async def test_plan_approve_not_plan_review(client):
    """Approving a task not in plan_review state should return 400."""
    create_resp = await client.post("/api/tasks", json={
        "title": "T", "description": "d", "target_repo": "/tmp",
    })
    task_id = create_resp.json()["id"]
    resp = await client.post(f"/api/tasks/{task_id}/plan/approve")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_plan_reject_not_plan_review(client):
    """Rejecting a task not in plan_review state should return 400."""
    create_resp = await client.post("/api/tasks", json={
        "title": "T", "description": "d", "target_repo": "/tmp",
    })
    task_id = create_resp.json()["id"]
    resp = await client.post(f"/api/tasks/{task_id}/plan/reject")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_plan_approve_success(client, session_factory):
    """Approving a plan-mode task in plan_review state should succeed."""
    create_resp = await client.post("/api/tasks", json={
        "title": "Plan Task", "description": "d", "target_repo": "/tmp", "mode": "plan",
    })
    task_id = create_resp.json()["id"]

    # Set task to plan_review state directly in DB
    async with session_factory() as db:
        await db.execute(
            update(Task).where(Task.id == task_id).values(
                status="plan_review", plan_content="Here is my plan..."
            )
        )
        await db.commit()

    resp = await client.post(f"/api/tasks/{task_id}/plan/approve")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["plan_approved"] is True


@pytest.mark.asyncio
async def test_plan_reject_success(client, session_factory):
    """Rejecting a plan-mode task in plan_review state should cancel it."""
    create_resp = await client.post("/api/tasks", json={
        "title": "Plan Task", "description": "d", "target_repo": "/tmp", "mode": "plan",
    })
    task_id = create_resp.json()["id"]

    async with session_factory() as db:
        await db.execute(
            update(Task).where(Task.id == task_id).values(
                status="plan_review", plan_content="Here is my plan..."
            )
        )
        await db.commit()

    resp = await client.post(f"/api/tasks/{task_id}/plan/reject")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelled"
    assert data["plan_approved"] is False


@pytest.mark.asyncio
async def test_plan_approve_not_found(client):
    resp = await client.post("/api/tasks/9999/plan/approve")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_plan_reject_not_found(client):
    resp = await client.post("/api/tasks/9999/plan/reject")
    assert resp.status_code == 404
