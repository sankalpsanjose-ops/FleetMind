from __future__ import annotations
import anthropic
from backend.game.models import AttackGrid, Coordinate
from backend.ai.provider import AIProvider, GameContext, MoveDecision, register_provider
from backend.ai.move_request import MoveRequestBuilder
from backend.ai.prompts import get_system_prompt, build_user_message
from backend.config import settings

THINKING_MODELS = {"claude-opus-4-7"}
DEFAULT_MODEL = "claude-sonnet-4-6"

@register_provider
class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, model: str | None = None):
        self.model = model or DEFAULT_MODEL
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key or "sk-placeholder"
        )

    async def decide_move(
        self,
        attack_grid: AttackGrid,
        context: GameContext,
        candidates: list[Coordinate] | None = None,
    ) -> MoveDecision:
        prompt_ctx = MoveRequestBuilder.build_prompt_context(attack_grid, context, candidates)
        system_prompt = get_system_prompt(context.difficulty)
        user_message = build_user_message(prompt_ctx)

        if self.model in THINKING_MODELS:
            return await self._decide_with_thinking(
                system_prompt, user_message, attack_grid, context
            )

        response = await self._client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=256,
        )
        content = response.content[0].text.strip()
        coordinate = MoveRequestBuilder.parse_coordinate(content, context.board_size)
        coordinate = self._safe_coord(coordinate, attack_grid)
        reasoning = content if context.show_reasoning else None
        return MoveDecision(coordinate=coordinate, reasoning=reasoning)

    async def _decide_with_thinking(
        self, system_prompt: str, user_message: str,
        attack_grid: AttackGrid, context: GameContext,
    ) -> MoveDecision:
        response = await self._client.messages.create(
            model=self.model,
            thinking={"type": "enabled", "budget_tokens": 5000},
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=8000,
        )
        thinking_text = ""
        coord_text = ""
        for block in response.content:
            if block.type == "thinking":
                thinking_text = block.thinking
            elif block.type == "text":
                coord_text = block.text.strip()

        coordinate = MoveRequestBuilder.parse_coordinate(coord_text, context.board_size)
        coordinate = self._safe_coord(coordinate, attack_grid)
        # Show the internal reasoning when requested — that's the interesting part
        reasoning = thinking_text if context.show_reasoning else None
        return MoveDecision(coordinate=coordinate, reasoning=reasoning)

    def _safe_coord(self, coord: Coordinate, attack_grid: AttackGrid) -> Coordinate:
        if attack_grid.get(coord).value != "unknown":
            unknown = attack_grid.unknown_cells()
            return unknown[0] if unknown else coord
        return coord
