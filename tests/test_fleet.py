import pytest
from backend.game.models import (
    Coordinate, Orientation, ShipType, Ship, FleetState,
    BoardSize, DifficultyMode
)
from backend.game.fleet import FleetManager, PlacementError, FLEET_CONFIG

def test_fleet_config_coverage():
    """Each non-asymmetric difficulty mode stays within 9-24% coverage for standard board."""
    for mode in DifficultyMode:
        if mode == DifficultyMode.GUERRILLA:
            continue  # Asymmetric mode — carrier side intentionally low coverage
        config = FLEET_CONFIG[mode][BoardSize.STANDARD]
        total_cells = sum(s.size for s in config)
        coverage = total_cells / (10 * 10)
        assert 0.09 <= coverage <= 0.24, f"{mode}: coverage {coverage:.2%} out of range"

def test_valid_placement():
    manager = FleetManager(board_size=10)
    ship = Ship(ShipType.CARRIER, Orientation.HORIZONTAL, Coordinate(0, 0))
    fleet = FleetState(size=10)
    manager.place_ship(fleet, ship)
    assert len(fleet.ships) == 1

def test_out_of_bounds_rejected():
    manager = FleetManager(board_size=10)
    ship = Ship(ShipType.CARRIER, Orientation.HORIZONTAL, Coordinate(0, 7))
    fleet = FleetState(size=10)
    with pytest.raises(PlacementError, match="out of bounds"):
        manager.place_ship(fleet, ship)

def test_overlap_rejected():
    manager = FleetManager(board_size=10)
    fleet = FleetState(size=10)
    ship1 = Ship(ShipType.CARRIER, Orientation.HORIZONTAL, Coordinate(0, 0))
    ship2 = Ship(ShipType.BATTLESHIP, Orientation.HORIZONTAL, Coordinate(0, 2))
    manager.place_ship(fleet, ship1)
    with pytest.raises(PlacementError, match="overlap"):
        manager.place_ship(fleet, ship2)

def test_adjacency_gap_enforced_admiral_plus():
    """Admiral+ requires 1 cell gap between ships."""
    manager = FleetManager(board_size=10, require_gap=True)
    fleet = FleetState(size=10)
    ship1 = Ship(ShipType.PATROL, Orientation.HORIZONTAL, Coordinate(0, 0))
    ship2 = Ship(ShipType.PATROL, Orientation.HORIZONTAL, Coordinate(1, 0))
    manager.place_ship(fleet, ship1)
    with pytest.raises(PlacementError, match="gap"):
        manager.place_ship(fleet, ship2)

def test_random_placement_produces_valid_fleet():
    manager = FleetManager(board_size=10)
    fleet = manager.place_fleet_random(DifficultyMode.COMMANDER, BoardSize.STANDARD)
    occupied = set()
    for ship in fleet.ships:
        for cell in ship.occupied_cells():
            assert cell not in occupied, "Overlap in random placement"
            assert cell.is_valid(10), "Out of bounds in random placement"
            occupied.add(cell)
