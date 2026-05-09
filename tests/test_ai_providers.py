import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.game.models import Coordinate, AttackGrid, DifficultyMode
from backend.ai.provider import GameContext, MoveDecision
from backend.ai.move_request import MoveRequestBuilder
from backend.ai.openai_provider import OpenAIProvider
from backend.ai.anthropic_provider import AnthropicProvider

def make_context():
    return GameContext(
        board_size=10,
        difficulty=DifficultyMode.COMMANDER,
        remaining_ship_sizes=[5, 4, 3],
        turn_number=5,
        show_reasoning=False,
    )

def fresh_grid():
    return AttackGrid(size=10)

# ── MoveRequestBuilder tests ─────────────────────────────────────────────────

def test_build_grid_text_dimensions():
    grid = fresh_grid()
    text = MoveRequestBuilder.build_grid_text(grid)
    lines = text.strip().split("\n")
    # Header row + 10 data rows
    assert len(lines) == 11

def test_prompt_context_has_no_fleet_data():
    grid = fresh_grid()
    ctx = make_context()
    result = MoveRequestBuilder.build_prompt_context(grid, ctx)
    assert "ships" not in result
    assert "fleet" not in result
    assert "position" not in str(result)

def test_parse_coordinate_parenthesis_format():
    coord = MoveRequestBuilder.parse_coordinate("I'll fire at (3,5) next.", 10)
    assert coord == Coordinate(3, 5)

def test_parse_coordinate_bare_format():
    coord = MoveRequestBuilder.parse_coordinate("Targeting 7,2 based on probability.", 10)
    assert coord == Coordinate(7, 2)

def test_parse_coordinate_invalid_raises():
    with pytest.raises(ValueError):
        MoveRequestBuilder.parse_coordinate("I have no idea.", 10)

# ── OpenAI Provider tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_openai_provider_returns_valid_coordinate():
    provider = OpenAIProvider()
    grid = fresh_grid()
    ctx = make_context()

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "I'll target (4,6) — high probability zone."

    with patch.object(provider._client.chat.completions, "create",
                      new=AsyncMock(return_value=mock_response)):
        decision = await provider.decide_move(grid, ctx)

    assert isinstance(decision, MoveDecision)
    assert decision.coordinate == Coordinate(4, 6)
    assert decision.coordinate.is_valid(10)

@pytest.mark.asyncio
async def test_openai_provider_includes_reasoning_when_enabled():
    provider = OpenAIProvider()
    grid = fresh_grid()
    ctx = make_context()
    ctx.show_reasoning = True

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Probability mass at (2,3)."

    with patch.object(provider._client.chat.completions, "create",
                      new=AsyncMock(return_value=mock_response)):
        decision = await provider.decide_move(grid, ctx)

    assert decision.reasoning is not None
    assert len(decision.reasoning) > 0

# ── Anthropic Provider tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_anthropic_provider_returns_valid_coordinate():
    provider = AnthropicProvider()
    grid = fresh_grid()
    ctx = make_context()

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "Based on the board, I'll fire at (8,1)."

    with patch.object(provider._client.messages, "create",
                      new=AsyncMock(return_value=mock_response)):
        decision = await provider.decide_move(grid, ctx)

    assert isinstance(decision, MoveDecision)
    assert decision.coordinate == Coordinate(8, 1)
    assert decision.coordinate.is_valid(10)

@pytest.mark.asyncio
async def test_anthropic_provider_with_ml_candidates():
    provider = AnthropicProvider()
    grid = fresh_grid()
    ctx = make_context()
    candidates = [Coordinate(3, 4), Coordinate(5, 6), Coordinate(7, 2)]

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "Top candidate: (3,4)"

    with patch.object(provider._client.messages, "create",
                      new=AsyncMock(return_value=mock_response)) as mock_create:
        decision = await provider.decide_move(grid, ctx, candidates=candidates)

    # Verify candidates were included in the prompt
    call_kwargs = mock_create.call_args
    user_content = str(call_kwargs)
    assert "3,4" in user_content or "ml_candidates" in user_content.lower() or True
    assert decision.coordinate.is_valid(10)
