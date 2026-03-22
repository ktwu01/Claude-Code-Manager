"""Tests for /api/tags endpoints."""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_list_tags_empty(client: AsyncClient):
    res = await client.get("/api/tags")
    assert res.status_code == 200
    assert res.json() == []


async def test_create_tag(client: AsyncClient):
    res = await client.post("/api/tags", json={"name": "frontend", "color": "sky"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "frontend"
    assert data["color"] == "sky"
    assert data["id"] > 0


async def test_create_tag_default_color(client: AsyncClient):
    res = await client.post("/api/tags", json={"name": "backend"})
    assert res.status_code == 201
    assert res.json()["color"] == "indigo"


async def test_create_tag_duplicate(client: AsyncClient):
    await client.post("/api/tags", json={"name": "dup-tag"})
    res = await client.post("/api/tags", json={"name": "dup-tag"})
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


async def test_list_tags_sorted(client: AsyncClient):
    await client.post("/api/tags", json={"name": "zeta", "color": "rose"})
    await client.post("/api/tags", json={"name": "alpha", "color": "cyan"})
    res = await client.get("/api/tags")
    names = [t["name"] for t in res.json()]
    assert names == sorted(names)


async def test_update_tag_color(client: AsyncClient):
    create = await client.post("/api/tags", json={"name": "color-test", "color": "indigo"})
    tag_id = create.json()["id"]
    res = await client.put(f"/api/tags/{tag_id}", json={"color": "emerald"})
    assert res.status_code == 200
    assert res.json()["color"] == "emerald"
    assert res.json()["name"] == "color-test"


async def test_update_tag_rename(client: AsyncClient):
    create = await client.post("/api/tags", json={"name": "old-name"})
    tag_id = create.json()["id"]
    res = await client.put(f"/api/tags/{tag_id}", json={"name": "new-name"})
    assert res.status_code == 200
    assert res.json()["name"] == "new-name"


async def test_rename_tag_updates_projects(client: AsyncClient):
    """Renaming a tag should update all projects that have it."""
    # Create tag
    create = await client.post("/api/tags", json={"name": "rename-me", "color": "amber"})
    tag_id = create.json()["id"]

    # Create project with this tag
    proj = await client.post("/api/projects", json={"name": "proj-rename-test", "tags": ["rename-me", "keep"]})
    assert proj.status_code == 201
    proj_id = proj.json()["id"]

    # Rename tag
    await client.put(f"/api/tags/{tag_id}", json={"name": "renamed"})

    # Verify project tags updated
    proj_res = await client.get(f"/api/projects/{proj_id}")
    assert "renamed" in proj_res.json()["tags"]
    assert "rename-me" not in proj_res.json()["tags"]
    assert "keep" in proj_res.json()["tags"]


async def test_rename_tag_duplicate_rejected(client: AsyncClient):
    await client.post("/api/tags", json={"name": "tag-a"})
    create_b = await client.post("/api/tags", json={"name": "tag-b"})
    tag_b_id = create_b.json()["id"]
    res = await client.put(f"/api/tags/{tag_b_id}", json={"name": "tag-a"})
    assert res.status_code == 400


async def test_delete_tag(client: AsyncClient):
    create = await client.post("/api/tags", json={"name": "del-me"})
    tag_id = create.json()["id"]
    res = await client.delete(f"/api/tags/{tag_id}")
    assert res.status_code == 200
    assert res.json()["ok"] is True

    # Verify gone
    tags = await client.get("/api/tags")
    assert not any(t["name"] == "del-me" for t in tags.json())


async def test_delete_tag_removes_from_projects(client: AsyncClient):
    """Deleting a tag should remove it from all projects."""
    create = await client.post("/api/tags", json={"name": "remove-me"})
    tag_id = create.json()["id"]

    proj = await client.post("/api/projects", json={"name": "proj-delete-test", "tags": ["remove-me", "stay"]})
    proj_id = proj.json()["id"]

    await client.delete(f"/api/tags/{tag_id}")

    proj_res = await client.get(f"/api/projects/{proj_id}")
    assert "remove-me" not in proj_res.json()["tags"]
    assert "stay" in proj_res.json()["tags"]


async def test_update_nonexistent_tag(client: AsyncClient):
    res = await client.put("/api/tags/99999", json={"color": "rose"})
    assert res.status_code == 404


async def test_delete_nonexistent_tag(client: AsyncClient):
    res = await client.delete("/api/tags/99999")
    assert res.status_code == 404
