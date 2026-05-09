from __future__ import annotations
import asyncio
import os
import copy
from backend.game.models import Coordinate, CellState, AttackGrid
from backend.ml.qlearning import QLearningAgent

CHECKPOINT_DIR = os.environ.get("ML_CHECKPOINT_DIR", "ml_checkpoints")
CHECKPOINT_PATH = os.path.join(CHECKPOINT_DIR, "qlearning.pkl")

_agent: QLearningAgent | None = None

def get_agent(board_size: int = 10) -> QLearningAgent:
    """Load or initialize the global RL agent."""
    global _agent
    if _agent is None:
        _agent = QLearningAgent(board_size=board_size)
        if os.path.exists(CHECKPOINT_PATH):
            _agent.load(CHECKPOINT_PATH)
    return _agent

async def train_on_game(
    board_size: int,
    shot_sequence: list[dict],  # [{"coord": Coordinate, "result": str, "side": str}]
    winner: str,
) -> None:
    """
    Async post-game training. Non-blocking — called after match is saved to DB.
    Replays the shot sequence through the Q-learning update loop.
    """
    agent = get_agent(board_size)

    # Reconstruct grids by replaying shots turn by turn
    grid = AttackGrid(size=board_size)

    for i, shot in enumerate(shot_sequence):
        coord = shot["coord"]
        result = shot["result"]
        side = shot["side"]
        game_won = (i == len(shot_sequence) - 1) and (
            (side == "player1" and winner == "player1") or
            (side == "player2" and winner == "player2")
        )

        prev_grid_snapshot = copy.deepcopy(grid)

        # Apply shot to grid
        if result == "miss":
            grid.set(coord, CellState.MISS)
        elif result in ("hit", "sunk"):
            grid.set(coord, CellState.HIT if result == "hit" else CellState.SUNK)

        agent.update(prev_grid_snapshot, coord, result, grid, game_won=game_won)

        # Yield control back to event loop periodically
        if i % 10 == 0:
            await asyncio.sleep(0)

    # Save checkpoint
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    agent.save(CHECKPOINT_PATH)
