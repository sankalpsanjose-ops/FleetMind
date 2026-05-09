import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, patch, MagicMock

from backend.main import app
from backend.db.database import Base, get_db
from backend.api.orchestrator import get_orchestrator, GameOrchestrator
from backend.ai.provider import MoveDecision
from backend.game.models import Coordinate

# Use in-memory DB with StaticPool for async-safe testing
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(test_engine)
TestSession = sessionmaker(bind=test_engine)

def override_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_db

@pytest.fixture
def fresh_orchestrator():
    orch = GameOrchestrator()
    app.dependency_overrides[get_orchestrator] = lambda: orch
    yield orch
    app.dependency_overrides.pop(get_orchestrator, None)

@pytest.mark.asyncio
async def test_health(fresh_orchestrator):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_create_game(fresh_orchestrator):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/games", json={
            "board_size": "standard",
            "difficulty": "commander",
            "player1_type": "human",
            "player2_type": "ai",
            "ai_provider_2": "anthropic",
            "ai_mode_2": "pure",
        })
    assert r.status_code == 200
    data = r.json()
    assert "game_id" in data
    assert data["phase"] == "placement"

@pytest.mark.asyncio
async def test_place_fleet_and_get_state(fresh_orchestrator):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/games", json={
            "board_size": "standard", "difficulty": "commander",
            "player1_type": "human", "player2_type": "ai",
            "ai_provider_2": "anthropic", "ai_mode_2": "pure",
        })
        game_id = r.json()["game_id"]

        place_r = await client.post(f"/games/{game_id}/placement", json={"ships": [
            {"ship_type": "carrier",    "orientation": "horizontal", "row": 0, "col": 0},
            {"ship_type": "battleship", "orientation": "horizontal", "row": 2, "col": 0},
            {"ship_type": "cruiser",    "orientation": "horizontal", "row": 4, "col": 0},
            {"ship_type": "submarine",  "orientation": "horizontal", "row": 6, "col": 0},
            {"ship_type": "patrol",     "orientation": "horizontal", "row": 8, "col": 0},
        ]})
        assert place_r.status_code == 200
        assert place_r.json()["phase"] == "battle"

        state_r = await client.get(f"/games/{game_id}/state")
        assert state_r.status_code == 200
        state = state_r.json()
        assert state["phase"] == "battle"
        assert "attack_grid" in state
        assert "fleet" not in state  # Anti-cheat: fleet never exposed via API

@pytest.mark.asyncio
async def test_human_fire(fresh_orchestrator):
    mock_decision = MoveDecision(coordinate=Coordinate(9, 9), reasoning=None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/games", json={
            "board_size": "standard", "difficulty": "commander",
            "player1_type": "human", "player2_type": "ai",
            "ai_provider_2": "anthropic", "ai_mode_2": "pure",
        })
        game_id = r.json()["game_id"]

        await client.post(f"/games/{game_id}/placement", json={"ships": [
            {"ship_type": "carrier",    "orientation": "horizontal", "row": 0, "col": 0},
            {"ship_type": "battleship", "orientation": "horizontal", "row": 2, "col": 0},
            {"ship_type": "cruiser",    "orientation": "horizontal", "row": 4, "col": 0},
            {"ship_type": "submarine",  "orientation": "horizontal", "row": 6, "col": 0},
            {"ship_type": "patrol",     "orientation": "horizontal", "row": 8, "col": 0},
        ]})

        with patch("backend.api.orchestrator.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.decide_move = AsyncMock(return_value=mock_decision)
            mock_get.return_value = mock_provider
            fire_r = await client.post(f"/games/{game_id}/fire", json={"row": 5, "col": 5})

    assert fire_r.status_code == 200
    event = fire_r.json()
    assert event["result"] in ("hit", "miss", "sunk")

@pytest.mark.asyncio
async def test_win_rates_endpoint(fresh_orchestrator):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/matches/win-rates")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)

@pytest.mark.asyncio
async def test_invalid_game_id_returns_404(fresh_orchestrator):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/games/no-such-game/state")
    assert r.status_code == 404
