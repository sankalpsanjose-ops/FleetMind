from __future__ import annotations
import random as _random
from openai import AsyncOpenAI
from backend.game.models import AttackGrid, Coordinate
from backend.ai.provider import AIProvider, GameContext, MoveDecision, register_provider
from backend.ai.move_request import MoveRequestBuilder
from backend.ai.prompts import get_system_prompt, build_user_message
from backend.config import settings

REASONING_MODELS = {"o1", "o3-mini", "o4-mini"}
DEFAULT_MODEL = "gpt-4o"

@register_provider
class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, model: str | None = None):
        self.model = model or DEFAULT_MODEL
        self._client = AsyncOpenAI(api_key=settings.openai_api_key or "sk-placeholder")

    async def decide_move(
        self,
        attack_grid: AttackGrid,
        context: GameContext,
        candidates: list[Coordinate] | None = None,
    ) -> MoveDecision:
        try:
            prompt_ctx = MoveRequestBuilder.build_prompt_context(attack_grid, context, candidates)
            system_prompt = get_system_prompt(context.difficulty)
            user_message = build_user_message(prompt_ctx)

            if self.model in REASONING_MODELS:
                response = await self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_message},
                    ],
                    max_completion_tokens=2000,
                )
            else:
                response = await self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_message},
                    ],
                    max_tokens=256,
                    temperature=0.3,
                )

            content = (response.choices[0].message.content or "").strip()
            coordinate, reasoning = MoveRequestBuilder.parse_response(content, context.board_size)

            if attack_grid.get(coordinate).value != "unknown":
                unknown = attack_grid.unknown_cells()
                coordinate = _random.choice(unknown) if unknown else coordinate

            return MoveDecision(
                coordinate=coordinate,
                reasoning=reasoning if context.show_reasoning else None,
            )

        except Exception:
            unknown = attack_grid.unknown_cells()
            coord = _random.choice(unknown) if unknown else Coordinate(0, 0)
            return MoveDecision(coordinate=coord, reasoning=None)
