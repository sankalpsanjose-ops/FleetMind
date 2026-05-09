import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from backend.game.models import BoardSize, DifficultyMode, Coordinate, GamePhase
from backend.ai.provider import MoveDecision
from backend.api.orchestrator import GameOrchestrator, GameSession, AIMode

@pytest.fixture
def orchestrator():
    return GameOrchestrator()

@pytest.mark.asyncio
async def test_create_human_vs_ai_session(orchestrator):
    session = await orchestrator.create_session(
        board_size=BoardSize.STANDARD,
        difficulty=DifficultyMode.COMMANDER,
        player1_type="human",
        player2_type="ai",
        ai_provider_1=None,
        ai_mode_1=None,
        ai_provider_2="anthropic",
        ai_mode_2=AIMode.PURE,
    )
    assert session.game_id is not None
    assert session.engine.state.phase == GamePhase.PLACEMENT

@pytest.mark.asyncio
async def test_create_ai_vs_ai_session(orchestrator):
    session = await orchestrator.create_session(
        board_size=BoardSize.STANDARD,
        difficulty=DifficultyMode.COMMANDER,
        player1_type="ai",
        player2_type="ai",
        ai_provider_1="openai",
        ai_mode_1=AIMode.PURE,
        ai_provider_2="anthropic",
        ai_mode_2=AIMode.PURE,
    )
    assert session.game_id is not None
    # Both AI fleets placed automatically
    assert session.engine.state.phase == GamePhase.BATTLE

@pytest.mark.asyncio
async def test_human_fleet_placement(orchestrator):
    session = await orchestrator.create_session(
        board_size=BoardSize.STANDARD,
        difficulty=DifficultyMode.COMMANDER,
        player1_type="human",
        player2_type="ai",
        ai_provider_1=None, ai_mode_1=None,
        ai_provider_2="anthropic", ai_mode_2=AIMode.PURE,
    )
    ships = [
        {"ship_type": "carrier", "orientation": "horizontal", "row": 0, "col": 0},
        {"ship_type": "battleship", "orientation": "horizontal", "row": 2, "col": 0},
        {"ship_type": "cruiser", "orientation": "horizontal", "row": 4, "col": 0},
        {"ship_type": "submarine", "orientation": "horizontal", "row": 6, "col": 0},
        {"ship_type": "patrol", "orientation": "horizontal", "row": 8, "col": 0},
    ]
    await orchestrator.place_human_fleet(session.game_id, ships)
    assert session.engine.state.phase == GamePhase.BATTLE

@pytest.mark.asyncio
async def test_human_fire_returns_event(orchestrator):
    session = await orchestrator.create_session(
        board_size=BoardSize.STANDARD,
        difficulty=DifficultyMode.COMMANDER,
        player1_type="human",
        player2_type="ai",
        ai_provider_1=None, ai_mode_1=None,
        ai_provider_2="anthropic", ai_mode_2=AIMode.PURE,
    )
    ships = [
        {"ship_type": "carrier", "orientation": "horizontal", "row": 0, "col": 0},
        {"ship_type": "battleship", "orientation": "horizontal", "row": 2, "col": 0},
        {"ship_type": "cruiser", "orientation": "horizontal", "row": 4, "col": 0},
        {"ship_type": "submarine", "orientation": "horizontal", "row": 6, "col": 0},
        {"ship_type": "patrol", "orientation": "horizontal", "row": 8, "col": 0},
    ]
    await orchestrator.place_human_fleet(session.game_id, ships)

    mock_decision = MoveDecision(coordinate=Coordinate(9, 9), reasoning=None)
    with patch("backend.api.orchestrator.get_provider") as mock_get:
        mock_provider = AsyncMock()
        mock_provider.decide_move = AsyncMock(return_value=mock_decision)
        mock_get.return_value = mock_provider
        event = await orchestrator.human_fire(session.game_id, row=5, col=5)

    assert event["result"] in ("hit", "miss", "sunk")
    assert "row" in event and "col" in event

@pytest.mark.asyncio
async def test_get_state_returns_attack_grid_only(orchestrator):
    session = await orchestrator.create_session(
        board_size=BoardSize.STANDARD,
        difficulty=DifficultyMode.COMMANDER,
        player1_type="human",
        player2_type="ai",
        ai_provider_1=None, ai_mode_1=None,
        ai_provider_2="anthropic", ai_mode_2=AIMode.PURE,
    )
    state = orchestrator.get_state(session.game_id)
    assert "fleet" not in state
    assert "ships" not in state
    assert "attack_grid" in state or "phase" in state
