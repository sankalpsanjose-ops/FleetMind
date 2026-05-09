from __future__ import annotations
import numpy as np
from backend.game.models import AttackGrid, Coordinate, CellState
from backend.ml.strategy import MLStrategy

class ProbabilityHeatmap(MLStrategy):
    """
    Hunt/Target + parity probability heatmap.

    For each unknown cell, counts how many valid ship placements pass through it
    given all known hits and misses. Parity filter eliminates cells unreachable
    by the smallest remaining ship. After a hit, concentrates scores along the
    hit axis until the ship is sunk.
    """

    def __init__(self, board_size: int, remaining_ships: list[int]):
        self.board_size = board_size
        self.remaining_ships = list(remaining_ships)
        self._hit_cells: list[Coordinate] = []
        self._active_axis: str | None = None  # "horizontal" | "vertical" | None

    def _is_horizontal_run(self) -> bool:
        if len(self._hit_cells) < 2:
            return False
        return self._hit_cells[0].row == self._hit_cells[1].row

    def _is_vertical_run(self) -> bool:
        if len(self._hit_cells) < 2:
            return False
        return self._hit_cells[0].col == self._hit_cells[1].col

    def score_cells(self, attack_grid: AttackGrid) -> dict[Coordinate, float]:
        size = self.board_size
        board = np.zeros((size, size), dtype=np.float64)
        min_ship = min(self.remaining_ships) if self.remaining_ships else 1

        # Mark known non-unknown cells so ship placements avoid them
        blocked = np.zeros((size, size), dtype=bool)
        for r in range(size):
            for c in range(size):
                state = attack_grid.get(Coordinate(r, c))
                if state == CellState.MISS or state == CellState.SUNK:
                    blocked[r][c] = True

        # Count valid placements for each ship size through each cell
        for ship_size in set(self.remaining_ships):
            # Horizontal placements
            for r in range(size):
                for c in range(size - ship_size + 1):
                    cells = [(r, c + i) for i in range(ship_size)]
                    if any(blocked[rr][cc] for rr, cc in cells):
                        continue
                    for rr, cc in cells:
                        board[rr][cc] += 1.0

            # Vertical placements
            for r in range(size - ship_size + 1):
                for c in range(size):
                    cells = [(r + i, c) for i in range(ship_size)]
                    if any(blocked[rr][cc] for rr, cc in cells):
                        continue
                    for rr, cc in cells:
                        board[rr][cc] += 1.0

        # Parity filter — only in hunt mode (no active hits).
        # When we have hits, we're in target mode and know the ship's rough location.
        if min_ship >= 2 and not self._hit_cells:
            parity = (min_ship + 1) % 2
            for r in range(size):
                for c in range(size):
                    if (r + c) % 2 != parity:
                        board[r][c] *= 0.5

        # If there are active hits, boost axis-aligned neighbors strongly
        if self._hit_cells:
            boost = np.zeros((size, size), dtype=np.float64)
            for hit in self._hit_cells:
                hr, hc = hit.row, hit.col
                horizontal = self._is_horizontal_run() or not self._is_vertical_run()
                vertical = self._is_vertical_run() or not self._is_horizontal_run()

                if horizontal:
                    for dc in [-1, 1]:
                        nc = hc + dc
                        if 0 <= nc < size and not blocked[hr][nc]:
                            boost[hr][nc] += 3.0
                if vertical:
                    for dr in [-1, 1]:
                        nr = hr + dr
                        if 0 <= nr < size and not blocked[nr][hc]:
                            boost[nr][hc] += 3.0

            board = board + boost

        # Zero out non-unknown cells
        result: dict[Coordinate, float] = {}
        for r in range(size):
            for c in range(size):
                coord = Coordinate(r, c)
                if attack_grid.get(coord) == CellState.UNKNOWN and board[r][c] > 0:
                    result[coord] = float(board[r][c])

        return result

    def top_candidates(self, attack_grid: AttackGrid, n: int = 5) -> list[Coordinate]:
        scores = self.score_cells(attack_grid)
        return sorted(scores, key=lambda c: scores[c], reverse=True)[:n]

    def update(self, coord: Coordinate, result: str) -> None:
        if result == "hit":
            self._hit_cells.append(coord)
            if len(self._hit_cells) >= 2:
                if self._hit_cells[-1].row == self._hit_cells[-2].row:
                    self._active_axis = "horizontal"
                else:
                    self._active_axis = "vertical"
        elif result == "sunk":
            # Ship found and sunk — clear hit tracking for next ship
            self._hit_cells = []
            self._active_axis = None
            if self.remaining_ships:
                self.remaining_ships.pop()
        # miss: no hit state change needed
