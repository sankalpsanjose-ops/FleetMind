from __future__ import annotations
import random
from backend.game.models import (
    Coordinate, Orientation, ShipType, Ship, FleetState,
    BoardSize, DifficultyMode, SHIP_SIZES
)

class PlacementError(ValueError):
    pass

def _ship(t: ShipType) -> Ship:
    return Ship(t, Orientation.HORIZONTAL, Coordinate(0, 0))

# Fleet composition per difficulty per board size
# Bow position is a placeholder — randomized during placement
FLEET_CONFIG: dict[DifficultyMode, dict[BoardSize, list[Ship]]] = {
    DifficultyMode.CADET: {
        BoardSize.STANDARD: [
            _ship(ShipType.CARRIER), _ship(ShipType.CARRIER),
            _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP),
            _ship(ShipType.CRUISER),
        ],  # 22 cells / 100 = 22%
        BoardSize.LARGE: [
            _ship(ShipType.CARRIER), _ship(ShipType.CARRIER), _ship(ShipType.CARRIER),
            _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP),
            _ship(ShipType.CRUISER), _ship(ShipType.CRUISER),
        ],  # 39 cells / 225 = ~17%
        BoardSize.MASSIVE: [
            _ship(ShipType.CARRIER), _ship(ShipType.CARRIER),
            _ship(ShipType.CARRIER), _ship(ShipType.CARRIER),
            _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP),
            _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP),
            _ship(ShipType.CRUISER), _ship(ShipType.CRUISER), _ship(ShipType.CRUISER),
        ],  # 57 cells / 400 = ~14%
    },
    DifficultyMode.COMMANDER: {
        BoardSize.STANDARD: [
            _ship(ShipType.CARRIER), _ship(ShipType.BATTLESHIP),
            _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE), _ship(ShipType.PATROL),
        ],  # 17 cells / 100 = 17%
        BoardSize.LARGE: [
            _ship(ShipType.CARRIER), _ship(ShipType.BATTLESHIP),
            _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE), _ship(ShipType.PATROL),
            _ship(ShipType.DESTROYER), _ship(ShipType.FRIGATE), _ship(ShipType.SPEEDBOAT),
        ],  # 38 cells / 225 = ~17%
        BoardSize.MASSIVE: [
            _ship(ShipType.CARRIER), _ship(ShipType.CARRIER),
            _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP),
            _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE), _ship(ShipType.PATROL),
            _ship(ShipType.DESTROYER), _ship(ShipType.FRIGATE),
            _ship(ShipType.SPEEDBOAT), _ship(ShipType.CORVETTE),
        ],  # 68 cells / 400 = 17%
    },
    DifficultyMode.ADMIRAL: {
        BoardSize.STANDARD: [
            _ship(ShipType.BATTLESHIP), _ship(ShipType.CRUISER),
            _ship(ShipType.SUBMARINE), _ship(ShipType.PATROL), _ship(ShipType.PATROL),
        ],  # 15 cells / 100 = 15%
        BoardSize.LARGE: [
            _ship(ShipType.BATTLESHIP), _ship(ShipType.DESTROYER),
            _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE), _ship(ShipType.FRIGATE),
            _ship(ShipType.PATROL), _ship(ShipType.PATROL), _ship(ShipType.SPEEDBOAT),
        ],  # 33 cells / 225 = ~15%
        BoardSize.MASSIVE: [
            _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP),
            _ship(ShipType.DESTROYER), _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE),
            _ship(ShipType.FRIGATE), _ship(ShipType.FRIGATE),
            _ship(ShipType.PATROL), _ship(ShipType.PATROL),
            _ship(ShipType.SPEEDBOAT), _ship(ShipType.CORVETTE),
        ],  # 60 cells / 400 = 15%
    },
    DifficultyMode.WAR_VETERAN: {
        BoardSize.STANDARD: [
            _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE),
            _ship(ShipType.PATROL), _ship(ShipType.PATROL), _ship(ShipType.PATROL),
        ],  # 13 cells / 100 = 13%
        BoardSize.LARGE: [
            _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE), _ship(ShipType.FRIGATE),
            _ship(ShipType.PATROL), _ship(ShipType.PATROL),
            _ship(ShipType.SPEEDBOAT), _ship(ShipType.SPEEDBOAT), _ship(ShipType.CORVETTE),
        ],  # 29 cells / 225 = ~13%
        BoardSize.MASSIVE: [
            _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE), _ship(ShipType.FRIGATE),
            _ship(ShipType.FRIGATE), _ship(ShipType.PATROL), _ship(ShipType.PATROL),
            _ship(ShipType.PATROL), _ship(ShipType.SPEEDBOAT), _ship(ShipType.SPEEDBOAT),
            _ship(ShipType.CORVETTE), _ship(ShipType.CORVETTE),
        ],  # 52 cells / 400 = 13%
    },
    DifficultyMode.BLACK_OPS: {
        BoardSize.STANDARD: [
            _ship(ShipType.SUBMARINE),
            _ship(ShipType.PATROL), _ship(ShipType.PATROL),
            _ship(ShipType.PATROL), _ship(ShipType.PATROL),
        ],  # 11 cells / 100 = 11%
        BoardSize.LARGE: [
            _ship(ShipType.SUBMARINE), _ship(ShipType.FRIGATE),
            _ship(ShipType.PATROL), _ship(ShipType.PATROL),
            _ship(ShipType.SPEEDBOAT), _ship(ShipType.SPEEDBOAT),
            _ship(ShipType.CORVETTE), _ship(ShipType.CORVETTE),
        ],  # 23 cells / 225 = ~10%
        BoardSize.MASSIVE: [
            _ship(ShipType.SUBMARINE), _ship(ShipType.SUBMARINE),
            _ship(ShipType.FRIGATE), _ship(ShipType.PATROL), _ship(ShipType.PATROL),
            _ship(ShipType.PATROL), _ship(ShipType.SPEEDBOAT), _ship(ShipType.SPEEDBOAT),
            _ship(ShipType.CORVETTE), _ship(ShipType.CORVETTE), _ship(ShipType.CORVETTE),
        ],  # 40 cells / 400 = 10%
    },
    DifficultyMode.ARMADA: {
        BoardSize.STANDARD: [
            _ship(ShipType.CARRIER),
            _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP),
            _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE),
            _ship(ShipType.PATROL), _ship(ShipType.PATROL),
        ],  # 21 cells / 100 = 21%
        BoardSize.LARGE: [
            _ship(ShipType.CARRIER), _ship(ShipType.CARRIER),
            _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP), _ship(ShipType.DESTROYER),
            _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE),
            _ship(ShipType.FRIGATE), _ship(ShipType.PATROL),
        ],  # 45 cells / 225 = 20%
        BoardSize.MASSIVE: [
            _ship(ShipType.CARRIER), _ship(ShipType.CARRIER), _ship(ShipType.CARRIER),
            _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP), _ship(ShipType.BATTLESHIP),
            _ship(ShipType.DESTROYER), _ship(ShipType.CRUISER), _ship(ShipType.SUBMARINE),
            _ship(ShipType.FRIGATE), _ship(ShipType.PATROL), _ship(ShipType.SPEEDBOAT),
        ],  # 80 cells / 400 = 20%
    },
    DifficultyMode.GUERRILLA: {
        # Player 1 (carrier side): 1-2 Carriers
        # Player 2 (swarm side): handled by place_guerrilla_fleet
        BoardSize.STANDARD: [_ship(ShipType.CARRIER)],           # 5 cells
        BoardSize.LARGE:    [_ship(ShipType.CARRIER)],           # 5 cells
        BoardSize.MASSIVE:  [_ship(ShipType.CARRIER), _ship(ShipType.CARRIER)],  # 10 cells
    },
}

GUERRILLA_SMALL_FLEET: dict[BoardSize, list[ShipType]] = {
    BoardSize.STANDARD: [ShipType.PATROL] * 2 + [ShipType.CORVETTE] * 3,
    BoardSize.LARGE:    [ShipType.PATROL] * 3 + [ShipType.CORVETTE] * 2 + [ShipType.SPEEDBOAT] * 3,
    BoardSize.MASSIVE:  [ShipType.PATROL] * 4 + [ShipType.CORVETTE] * 4 + [ShipType.SPEEDBOAT] * 2,
}


class FleetManager:
    def __init__(self, board_size: int, require_gap: bool = False):
        self.board_size = board_size
        self.require_gap = require_gap

    def _occupied_cells(self, fleet: FleetState) -> set[Coordinate]:
        cells: set[Coordinate] = set()
        for ship in fleet.ships:
            cells.update(ship.occupied_cells())
        return cells

    def _buffer_cells(self, fleet: FleetState) -> set[Coordinate]:
        buffer: set[Coordinate] = set()
        for ship in fleet.ships:
            for cell in ship.occupied_cells():
                for neighbor in cell.neighbors():
                    if neighbor.is_valid(self.board_size):
                        buffer.add(neighbor)
        return buffer

    def place_ship(self, fleet: FleetState, ship: Ship) -> None:
        for cell in ship.occupied_cells():
            if not cell.is_valid(self.board_size):
                raise PlacementError(
                    f"Ship {ship.ship_type.value} extends out of bounds at {cell}"
                )

        occupied = self._occupied_cells(fleet)
        for cell in ship.occupied_cells():
            if cell in occupied:
                raise PlacementError(
                    f"Ship {ship.ship_type.value} would overlap at {cell}"
                )

        if self.require_gap:
            buffer = self._buffer_cells(fleet)
            for cell in ship.occupied_cells():
                if cell in buffer:
                    raise PlacementError(
                        f"Ship {ship.ship_type.value} violates 1-cell gap requirement at {cell}"
                    )

        fleet.ships.append(ship)

    def _random_ship(self, ship_type: ShipType) -> Ship:
        orientation = random.choice(list(Orientation))
        size = SHIP_SIZES[ship_type]
        if orientation == Orientation.HORIZONTAL:
            row = random.randint(0, self.board_size - 1)
            col = random.randint(0, self.board_size - size)
        else:
            row = random.randint(0, self.board_size - size)
            col = random.randint(0, self.board_size - 1)
        return Ship(ship_type, orientation, Coordinate(row, col))

    def place_fleet_random(self, difficulty: DifficultyMode, board_size: BoardSize) -> FleetState:
        fleet = FleetState(size=board_size.value)
        templates = FLEET_CONFIG[difficulty][board_size]
        for template in templates:
            placed = False
            for _ in range(1000):
                candidate = self._random_ship(template.ship_type)
                try:
                    self.place_ship(fleet, candidate)
                    placed = True
                    break
                except PlacementError:
                    continue
            if not placed:
                raise RuntimeError(
                    f"Could not place {template.ship_type} after 1000 attempts"
                )
        return fleet

    def place_guerrilla_fleet(self, side: str, board_size: BoardSize) -> FleetState:
        """side='carrier' gets 1-2 Carriers. side='swarm' gets many small ships."""
        fleet = FleetState(size=board_size.value)
        if side == "carrier":
            ship_types = [s.ship_type for s in FLEET_CONFIG[DifficultyMode.GUERRILLA][board_size]]
        else:
            ship_types = GUERRILLA_SMALL_FLEET[board_size]

        for ship_type in ship_types:
            placed = False
            for _ in range(1000):
                candidate = self._random_ship(ship_type)
                try:
                    self.place_ship(fleet, candidate)
                    placed = True
                    break
                except PlacementError:
                    continue
            if not placed:
                raise RuntimeError(f"Could not place {ship_type}")
        return fleet
