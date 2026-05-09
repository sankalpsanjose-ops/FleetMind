from __future__ import annotations
import pickle
import random
import numpy as np
from backend.game.models import AttackGrid, Coordinate, CellState

class QLearningAgent:
    """
    Tabular Q-learning agent for Battleship.

    State: tuple of cell states (0=unknown, 1=miss, 2=hit, 3=sunk) for all cells.
    Action: (row, col) coordinate to fire.
    Rewards: +1 hit, +5 ship sunk, +20 game won, -0.1 miss.

    The state space is large (4^100 for 10x10), so we use a dict-based sparse Q-table.
    Entries are created on first encounter and default to 0.0.
    """

    REWARDS = {"hit": 1.0, "sunk": 5.0, "win": 20.0, "miss": -0.1}
    ALPHA = 0.1     # learning rate
    GAMMA = 0.95    # discount factor
    EPSILON = 0.15  # exploration rate

    def __init__(self, board_size: int = 10):
        self.board_size = board_size
        self._q: dict[tuple, dict[tuple, float]] = {}

    def _encode_state(self, grid: AttackGrid) -> tuple:
        state = []
        for r in range(self.board_size):
            for c in range(self.board_size):
                s = grid.get(Coordinate(r, c))
                state.append(s.value)
        return tuple(state)

    def _get_q(self, grid: AttackGrid, coord: Coordinate) -> float:
        state = self._encode_state(grid)
        action = (coord.row, coord.col)
        return self._q.get(state, {}).get(action, 0.0)

    def _set_q(self, grid: AttackGrid, coord: Coordinate, value: float) -> None:
        state = self._encode_state(grid)
        action = (coord.row, coord.col)
        if state not in self._q:
            self._q[state] = {}
        self._q[state][action] = value

    def _max_q_next(self, next_grid: AttackGrid) -> float:
        state = self._encode_state(next_grid)
        if state not in self._q or not self._q[state]:
            return 0.0
        return max(self._q[state].values())

    def select_move(self, grid: AttackGrid) -> Coordinate:
        unknown = grid.unknown_cells()
        if not unknown:
            raise ValueError("No unknown cells left — game should be over")

        # Epsilon-greedy: explore randomly or exploit Q-table
        if random.random() < self.EPSILON:
            return random.choice(unknown)

        state = self._encode_state(grid)
        if state not in self._q:
            return random.choice(unknown)

        best_coord = None
        best_q = float("-inf")
        for coord in unknown:
            action = (coord.row, coord.col)
            q = self._q[state].get(action, 0.0)
            if q > best_q:
                best_q = q
                best_coord = coord

        return best_coord if best_coord is not None else random.choice(unknown)

    def update(
        self,
        prev_grid: AttackGrid,
        coord: Coordinate,
        result: str,
        next_grid: AttackGrid,
        game_won: bool = False,
    ) -> None:
        reward = self.REWARDS.get(result, 0.0)
        if game_won:
            reward += self.REWARDS["win"]

        current_q = self._get_q(prev_grid, coord)
        max_next = self._max_q_next(next_grid)
        new_q = current_q + self.ALPHA * (reward + self.GAMMA * max_next - current_q)
        self._set_q(prev_grid, coord, new_q)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self._q, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            self._q = pickle.load(f)
