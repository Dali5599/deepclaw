import pytest
from httpx import AsyncClient, ASGITransport
from backend.api.main import app
from backend.core import settings, get_llm_router
from backend.db.session import create_tables

@pytest.mark.asyncio
async def test_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "DeepClaw API"

@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "llm_router" in data["components"]
        assert "database" in data["components"]

@pytest.mark.asyncio
async def test_research_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test listing
        res_list = await ac.get("/api/research/list")
        assert res_list.status_code == 200
        assert "reports" in res_list.json()

        # Test start research
        res_start = await ac.post("/api/research/start", json={
            "topic": "Autonomous AI Multi-Agent Systems",
            "depth": 1,
            "max_sources": 5
        })
        assert res_start.status_code == 200
        session_id = res_start.json()["id"]
        assert session_id is not None

        # Test progress
        res_prog = await ac.get(f"/api/research/{session_id}/progress")
        assert res_prog.status_code == 200

@pytest.mark.asyncio
async def test_reports_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/reports/")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

def test_llm_router():
    router = get_llm_router()
    providers = router.get_available_providers()
    assert isinstance(providers, list)
    assert len(providers) >= 1
