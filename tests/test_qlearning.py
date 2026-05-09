import pytest
import tempfile, os
from backend.game.models import Coordinate, CellState, AttackGrid
from backend.ml.qlearning import QLearningAgent

def fresh_grid(size=10):
    return AttackGrid(size=size)

def test_agent_picks_unknown_cell():
    agent = QLearningAgent(board_size=10)
    grid = fresh_grid()
    coord = agent.select_move(grid)
    assert coord.is_valid(10)
    assert grid.get(coord) == CellState.UNKNOWN

def test_agent_avoids_already_fired_cells():
    agent = QLearningAgent(board_size=10)
    grid = fresh_grid()
    # Fill almost all cells
    for r in range(10):
        for c in range(10):
            if not (r == 5 and c == 5):
                grid.set(Coordinate(r, c), CellState.MISS)
    coord = agent.select_move(grid)
    assert coord == Coordinate(5, 5)

def test_reward_updates_q_table():
    agent = QLearningAgent(board_size=10)
    grid = fresh_grid()
    coord = Coordinate(3, 3)
    before = agent._get_q(grid, coord)
    agent.update(grid, coord, "hit", fresh_grid())
    after = agent._get_q(grid, coord)
    # Q-value should increase after a hit reward
    assert after > before

def test_miss_penalty_reduces_q_value():
    agent = QLearningAgent(board_size=10)
    grid = fresh_grid()
    coord = Coordinate(7, 7)
    # Force a known initial value
    agent._set_q(grid, coord, 0.5)
    agent.update(grid, coord, "miss", fresh_grid())
    after = agent._get_q(grid, coord)
    assert after < 0.5

def test_checkpoint_save_and_load(tmp_path):
    agent = QLearningAgent(board_size=10)
    grid = fresh_grid()
    # Give it some Q-values
    agent.update(grid, Coordinate(0, 0), "hit", fresh_grid())
    path = str(tmp_path / "checkpoint.pkl")
    agent.save(path)
    agent2 = QLearningAgent(board_size=10)
    agent2.load(path)
    # Loaded agent should have same Q-values
    q1 = agent._get_q(grid, Coordinate(0, 0))
    q2 = agent2._get_q(grid, Coordinate(0, 0))
    assert abs(q1 - q2) < 1e-6
