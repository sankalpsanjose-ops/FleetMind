import pytest
from backend.game.models import (
    Coordinate, Orientation, ShipType, Ship, Cell, CellState,
    AttackGrid, FleetState, BoardSize, DifficultyMode
)

def test_coordinate_in_bounds():
    coord = Coordinate(row=0, col=0)
    assert coord.is_valid(10)
    assert not Coordinate(row=10, col=0).is_valid(10)
    assert not Coordinate(row=0, col=-1).is_valid(10)

def test_ship_cells_horizontal():
    ship = Ship(ship_type=ShipType.CARRIER, orientation=Orientation.HORIZONTAL,
                bow=Coordinate(row=0, col=0))
    cells = ship.occupied_cells()
    assert len(cells) == 5
    assert cells[0] == Coordinate(row=0, col=0)
    assert cells[4] == Coordinate(row=0, col=4)

def test_ship_cells_vertical():
    ship = Ship(ship_type=ShipType.BATTLESHIP, orientation=Orientation.VERTICAL,
                bow=Coordinate(row=2, col=3))
    cells = ship.occupied_cells()
    assert len(cells) == 4
    assert cells[3] == Coordinate(row=5, col=3)

def test_attack_grid_never_exposes_fleet():
    grid = AttackGrid(size=10)
    # AttackGrid has no ship position data — only cell states
    assert not hasattr(grid, 'ships')
    assert not hasattr(grid, 'fleet')

def test_fleet_state_never_exposed_to_attack():
    fleet = FleetState(size=10)
    # FleetState has no attack result data
    assert not hasattr(fleet, 'hits')
    assert not hasattr(fleet, 'misses')

def test_board_size_values():
    assert BoardSize.STANDARD.value == 10
    assert BoardSize.LARGE.value == 15
    assert BoardSize.MASSIVE.value == 20
