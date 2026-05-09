from __future__ import annotations
from openai import AsyncOpenAI
from backend.game.models import AttackGrid, Coordinate
from backend.ai.provider import AIProvider, GameContext, MoveDecision, register_provider
from backend.ai.move_request import MoveRequestBuilder
from backend.ai.prompts import get_system_prompt, build_user_message
from backend.config import settings

@register_provider
class OpenAIProvider(AIProvider):
    name = "openai"
    model = "gpt-4o"

    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.openai_api_key or "sk-placeholder")

    async def decide_move(
        self,
        attack_grid: AttackGrid,
        context: GameContext,
        candidates: list[Coordinate] | None = None,
    ) -> MoveDecision:
        prompt_ctx = MoveRequestBuilder.build_prompt_context(attack_grid, context, candidates)
        system_prompt = get_system_prompt(context.difficulty)
        user_message = build_user_message(prompt_ctx)

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=256,
            temperature=0.3,
        )

        content = response.choices[0].message.content.strip()
        coordinate = MoveRequestBuilder.parse_coordinate(content, context.board_size)

        # Validate the coordinate is actually unknown — fallback if not
        if attack_grid.get(coordinate).value != "unknown":
            unknown = attack_grid.unknown_cells()
            coordinate = unknown[0] if unknown else coordinate

        reasoning = content if context.show_reasoning else None
        return MoveDecision(coordinate=coordinate, reasoning=reasoning)
