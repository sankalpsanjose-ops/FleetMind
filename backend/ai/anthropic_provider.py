from __future__ import annotations
import random as _random
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
        try:
            prompt_ctx   = MoveRequestBuilder.build_prompt_context(attack_grid, context, candidates)
            user_message = build_user_message(prompt_ctx)
            is_thinking  = self.model in THINKING_MODELS
            system_prompt = get_system_prompt(context.difficulty, thinking=is_thinking)

            if is_thinking:
                return await self._decide_with_thinking(
                    system_prompt, user_message, attack_grid, context
                )
            return await self._decide_standard(
                system_prompt, user_message, attack_grid, context
            )
        except Exception as exc:
            unknown = attack_grid.unknown_cells()
            coord   = _random.choice(unknown) if unknown else Coordinate(0, 0)
            # Surface the error in the reasoning panel so it's visible
            msg = f"[Error] {exc}" if context.show_reasoning else None
            return MoveDecision(coordinate=coord, reasoning=msg)

    async def _decide_with_thinking(
        self, system_prompt: str, user_message: str,
        attack_grid: AttackGrid, context: GameContext,
    ) -> MoveDecision:
        thinking_text = ""
        coord_text    = ""

        try:
            response = await self._client.messages.create(
                model=self.model,
                thinking={"type": "adaptive"},
                output_config={"effort": "high"},
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=16000,
            )
            for block in response.content:
                btype = getattr(block, "type", "")
                if btype == "thinking":
                    thinking_text = getattr(block, "thinking", "") or ""
                elif btype == "text":
                    coord_text = (getattr(block, "text", "") or "").strip()

        except Exception as exc:
            # API call itself failed — fall back to standard, but surface the error
            result = await self._decide_standard(system_prompt, user_message, attack_grid, context)
            if context.show_reasoning:
                return MoveDecision(
                    coordinate=result.coordinate,
                    reasoning=f"[Thinking API error: {exc}]",
                )
            return result

        if not coord_text:
            # Response had no text block — fall back to standard for coordinate,
            # but preserve any thinking we got as the reasoning.
            result = await self._decide_standard(system_prompt, user_message, attack_grid, context)
            if thinking_text and context.show_reasoning:
                return MoveDecision(coordinate=result.coordinate, reasoning=thinking_text)
            return result

        coordinate, text_reasoning = MoveRequestBuilder.parse_response(coord_text, context.board_size)
        coordinate = self._safe_coord(coordinate, attack_grid)
        reasoning  = (thinking_text or text_reasoning) if context.show_reasoning else None
        return MoveDecision(coordinate=coordinate, reasoning=reasoning)

    async def _decide_standard(
        self, system_prompt: str, user_message: str,
        attack_grid: AttackGrid, context: GameContext,
    ) -> MoveDecision:
        response = await self._client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=512,
        )
        coord_text = ""
        for block in response.content:
            btype = getattr(block, "type", "")
            if btype == "text":
                coord_text = (getattr(block, "text", "") or "").strip()
                break

        coordinate, reasoning = MoveRequestBuilder.parse_response(coord_text, context.board_size)
        coordinate = self._safe_coord(coordinate, attack_grid)
        return MoveDecision(
            coordinate=coordinate,
            reasoning=reasoning if context.show_reasoning else None,
        )

    def _safe_coord(self, coord: Coordinate, attack_grid: AttackGrid) -> Coordinate:
        if attack_grid.get(coord).value != "unknown":
            unknown = attack_grid.unknown_cells()
            return _random.choice(unknown) if unknown else coord
        return coord
