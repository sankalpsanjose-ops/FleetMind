from __future__ import annotations
from backend.game.models import AttackGrid, CellState, Coordinate
from backend.ai.provider import GameContext

class MoveRequestBuilder:
    """
    Serializes game state for the AI layer.
    ONLY touches AttackGrid — never FleetState.
    This is the anti-cheat gateway.
    """

    @staticmethod
    def build_grid_text(attack_grid: AttackGrid) -> str:
        """Render the attack grid as a human-readable string for LLM prompts."""
        size = attack_grid.size
        col_labels = "  " + " ".join(str(c) for c in range(size))
        rows = [col_labels]
        state_chars = {
            CellState.UNKNOWN: "·",
            CellState.MISS: "○",
            CellState.HIT: "X",
            CellState.SUNK: "#",
        }
        for r in range(size):
            row_str = f"{r} " + " ".join(
                state_chars[attack_grid.get(Coordinate(r, c))]
                for c in range(size)
            )
            rows.append(row_str)
        return "\n".join(rows)

    @staticmethod
    def build_prompt_context(
        attack_grid: AttackGrid,
        context: GameContext,
        candidates: list[Coordinate] | None = None,
    ) -> dict:
        """
        Returns a dict with everything needed to construct the LLM message.
        Contains ONLY derived information from AttackGrid — no fleet positions.
        """
        grid_text = MoveRequestBuilder.build_grid_text(attack_grid)
        hits = attack_grid.hit_cells()
        unknown = attack_grid.unknown_cells()

        prompt_ctx = {
            "board_size": context.board_size,
            "difficulty": context.difficulty.value,
            "turn_number": context.turn_number,
            "remaining_ship_sizes": sorted(context.remaining_ship_sizes, reverse=True),
            "grid_text": grid_text,
            "hit_count": len(hits),
            "unknown_count": len(unknown),
            "hit_coordinates": [f"({c.row},{c.col})" for c in hits],
        }

        if candidates:
            prompt_ctx["ml_candidates"] = [
                f"({c.row},{c.col})" for c in candidates
            ]

        return prompt_ctx

    @staticmethod
    def parse_coordinate(response_text: str, board_size: int) -> Coordinate:
        """
        Extract a coordinate from LLM response text.
        Looks for patterns like (3,5) or 3,5 or row=3 col=5.
        Falls back to first valid coordinate found.
        """
        import re
        # Try (row,col) pattern
        match = re.search(r'\((\d+)\s*,\s*(\d+)\)', response_text)
        if match:
            r, c = int(match.group(1)), int(match.group(2))
            coord = Coordinate(r, c)
            if coord.is_valid(board_size):
                return coord

        # Try bare row,col pattern
        match = re.search(r'\b(\d+)\s*,\s*(\d+)\b', response_text)
        if match:
            r, c = int(match.group(1)), int(match.group(2))
            coord = Coordinate(r, c)
            if coord.is_valid(board_size):
                return coord

        raise ValueError(f"Could not parse coordinate from: {response_text!r}")
