from __future__ import annotations
import re
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
        size = attack_grid.size
        col_labels = "  " + " ".join(str(c) for c in range(size))
        rows = [col_labels]
        state_chars = {
            CellState.UNKNOWN: "·",
            CellState.MISS:    "○",
            CellState.HIT:     "X",
            CellState.SUNK:    "#",
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
        grid_text = MoveRequestBuilder.build_grid_text(attack_grid)
        hits    = attack_grid.hit_cells()
        unknown = attack_grid.unknown_cells()

        prompt_ctx = {
            "board_size":           context.board_size,
            "difficulty":           context.difficulty.value,
            "turn_number":          context.turn_number,
            "remaining_ship_sizes": sorted(context.remaining_ship_sizes, reverse=True),
            "grid_text":            grid_text,
            "hit_count":            len(hits),
            "unknown_count":        len(unknown),
            "hit_coordinates":      [f"({c.row},{c.col})" for c in hits],
        }
        if candidates:
            prompt_ctx["ml_candidates"] = [f"({c.row},{c.col})" for c in candidates]
        return prompt_ctx

    @staticmethod
    def parse_response(response_text: str, board_size: int) -> tuple[Coordinate, str | None]:
        """
        Parse the REASON / FIRE format.  Falls back to bare-coordinate parsing for
        models that ignore the format instruction.
        Returns (coordinate, reasoning_or_None).
        """
        reasoning: str | None = None

        # Extract REASON line
        reason_m = re.search(r'REASON\s*:\s*(.+)', response_text, re.IGNORECASE)
        if reason_m:
            reasoning = reason_m.group(1).strip()

        # Extract coordinate from FIRE line first, then fall back to anywhere in the text
        fire_m = re.search(r'FIRE\s*:\s*(.+)', response_text, re.IGNORECASE)
        coord_text = fire_m.group(1).strip() if fire_m else response_text

        coordinate = MoveRequestBuilder.parse_coordinate(coord_text, board_size)
        return coordinate, reasoning

    @staticmethod
    def parse_coordinate(response_text: str, board_size: int) -> Coordinate:
        """Extract a coordinate from text. Tries (row,col) then bare row,col."""
        # (row,col) with optional spaces
        m = re.search(r'\((\d+)\s*,\s*(\d+)\)', response_text)
        if m:
            r, c = int(m.group(1)), int(m.group(2))
            coord = Coordinate(r, c)
            if coord.is_valid(board_size):
                return coord

        # bare row,col
        m = re.search(r'\b(\d+)\s*,\s*(\d+)\b', response_text)
        if m:
            r, c = int(m.group(1)), int(m.group(2))
            coord = Coordinate(r, c)
            if coord.is_valid(board_size):
                return coord

        raise ValueError(f"Could not parse coordinate from: {response_text!r}")
