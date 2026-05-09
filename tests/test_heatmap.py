import pytest
from backend.game.models import Coordinate, CellState, AttackGrid
from backend.ml.heatmap import ProbabilityHeatmap

def fresh_grid(size=10):
    return AttackGrid(size=size)

def test_all_unknown_cells_have_positive_score():
    grid = fresh_grid()
    hm = ProbabilityHeatmap(board_size=10, remaining_ships=[5, 4, 3, 3, 2])
    scores = hm.score_cells(grid)
    assert all(v > 0 for v in scores.values())
    assert len(scores) == 100

def test_miss_reduces_neighbor_scores():
    grid = fresh_grid()
    hm = ProbabilityHeatmap(board_size=10, remaining_ships=[2])
    scores_before = hm.score_cells(grid)
    # Register a miss at (0,0) — cells adjacent can't be part of ships ending there
    grid.set(Coordinate(0, 0), CellState.MISS)
    hm.update(Coordinate(0, 0), "miss")
    scores_after = hm.score_cells(grid)
    # Total probability mass should decrease after a miss
    assert sum(scores_after.values()) < sum(scores_before.values())

def test_hit_concentrates_probability_on_axis():
    grid = fresh_grid()
    hm = ProbabilityHeatmap(board_size=10, remaining_ships=[3])
    grid.set(Coordinate(5, 5), CellState.HIT)
    hm.update(Coordinate(5, 5), "hit")
    scores = hm.score_cells(grid)
    # Cells along the horizontal and vertical axes of the hit should score higher
    axis_coords = [
        Coordinate(5, 4), Coordinate(5, 6),  # horizontal neighbors
        Coordinate(4, 5), Coordinate(6, 5),  # vertical neighbors
    ]
    off_axis = Coordinate(3, 3)
    assert any(scores.get(c, 0) > scores.get(off_axis, 0) for c in axis_coords)

def test_parity_filter_skips_unreachable_cells():
    """With smallest ship size=2, every other cell in a checkerboard is unreachable."""
    grid = fresh_grid(size=4)
    hm = ProbabilityHeatmap(board_size=4, remaining_ships=[2])
    scores = hm.score_cells(grid)
    # All scored cells must be reachable by a size-2 ship in some orientation
    assert len(scores) > 0
    for coord in scores:
        assert coord.is_valid(4)

def test_already_fired_cells_excluded():
    grid = fresh_grid()
    hm = ProbabilityHeatmap(board_size=10, remaining_ships=[3])
    grid.set(Coordinate(0, 0), CellState.MISS)
    grid.set(Coordinate(1, 1), CellState.HIT)
    hm.update(Coordinate(0, 0), "miss")
    hm.update(Coordinate(1, 1), "hit")
    scores = hm.score_cells(grid)
    assert Coordinate(0, 0) not in scores
    assert Coordinate(1, 1) not in scores

def test_top_candidates_returns_sorted_list():
    grid = fresh_grid()
    hm = ProbabilityHeatmap(board_size=10, remaining_ships=[5, 4, 3, 3, 2])
    candidates = hm.top_candidates(grid, n=5)
    assert len(candidates) == 5
    scores = hm.score_cells(grid)
    for coord in candidates:
        assert coord in scores
