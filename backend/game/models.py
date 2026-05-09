from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List

class BoardSize(Enum):
    STANDARD = 10
    LARGE = 15
    MASSIVE = 20

class DifficultyMode(Enum):
    CADET = "cadet"
    COMMANDER = "commander"
    ADMIRAL = "admiral"
    WAR_VETERAN = "war_veteran"
    BLACK_OPS = "black_ops"
    ARMADA = "armada"
    GUERRILLA = "guerrilla"

class Orientation(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

class ShipType(Enum):
    CARRIER = "carrier"          # size 5
    BATTLESHIP = "battleship"    # size 4
    CRUISER = "cruiser"          # size 3
    SUBMARINE = "submarine"      # size 3
    PATROL = "patrol"            # size 2
    DESTROYER = "destroyer"      # size 4
    FRIGATE = "frigate"          # size 3
    SPEEDBOAT = "speedboat"      # size 2
    CORVETTE = "corvette"        # size 2

SHIP_SIZES: dict[ShipType, int] = {
    ShipType.CARRIER: 5,
    ShipType.BATTLESHIP: 4,
    ShipType.CRUISER: 3,
    ShipType.SUBMARINE: 3,
    ShipType.PATROL: 2,
    ShipType.DESTROYER: 4,
    ShipType.FRIGATE: 3,
    ShipType.SPEEDBOAT: 2,
    ShipType.CORVETTE: 2,
}

class CellState(Enum):
    UNKNOWN = "unknown"
    MISS = "miss"
    HIT = "hit"
    SUNK = "sunk"

# Alias for test import compatibility
Cell = CellState

@dataclass(frozen=True)
class Coordinate:
    row: int
    col: int

    def is_valid(self, board_size: int) -> bool:
        return 0 <= self.row < board_size and 0 <= self.col < board_size

    def neighbors(self) -> List[Coordinate]:
        return [
            Coordinate(self.row - 1, self.col),
            Coordinate(self.row + 1, self.col),
            Coordinate(self.row, self.col - 1),
            Coordinate(self.row, self.col + 1),
        ]

@dataclass
class Ship:
    ship_type: ShipType
    orientation: Orientation
    bow: Coordinate
    hits: set = field(default_factory=set)
    sunk: bool = False

    @property
    def size(self) -> int:
        return SHIP_SIZES[self.ship_type]

    def occupied_cells(self) -> List[Coordinate]:
        cells = []
        for i in range(self.size):
            if self.orientation == Orientation.HORIZONTAL:
                cells.append(Coordinate(self.bow.row, self.bow.col + i))
            else:
                cells.append(Coordinate(self.bow.row + i, self.bow.col))
        return cells

    def register_hit(self, coord: Coordinate) -> None:
        self.hits.add(coord)
        if len(self.hits) >= self.size:
            self.sunk = True

# ── Anti-cheat: Two completely separate data containers ──────────────────────
# FleetState owns ship positions. AttackGrid owns shot results.
# They share NO data. MoveRequestBuilder only ever touches AttackGrid.

@dataclass
class FleetState:
    """Owns ship positions. NEVER passed to AI layer."""
    size: int
    ships: List[Ship] = field(default_factory=list)

    def all_sunk(self) -> bool:
        return len(self.ships) > 0 and all(s.sunk for s in self.ships)

    def ship_at(self, coord: Coordinate):
        for ship in self.ships:
            if coord in ship.occupied_cells():
                return ship
        return None

@dataclass
class AttackGrid:
    """Owns shot results only. The ONLY data the AI ever sees."""
    size: int
    cells: dict = field(default_factory=dict)  # Coordinate -> CellState

    def get(self, coord: Coordinate) -> CellState:
        return self.cells.get(coord, CellState.UNKNOWN)

    def set(self, coord: Coordinate, state: CellState) -> None:
        self.cells[coord] = state

    def unknown_cells(self) -> List[Coordinate]:
        return [
            Coordinate(r, c)
            for r in range(self.size)
            for c in range(self.size)
            if self.get(Coordinate(r, c)) == CellState.UNKNOWN
        ]

    def hit_cells(self) -> List[Coordinate]:
        return [coord for coord, state in self.cells.items() if state == CellState.HIT]

class GamePhase(Enum):
    SETUP = "setup"
    PLACEMENT = "placement"
    BATTLE = "battle"
    GAME_OVER = "game_over"

@dataclass
class GameState:
    board_size: int
    difficulty: DifficultyMode
    phase: GamePhase = GamePhase.SETUP
    current_turn: str = "player1"   # "player1" | "player2"
    turn_number: int = 0
    winner: str | None = None
    # Fleets — never serialized to AI layer
    fleet_p1: FleetState = field(default_factory=lambda: FleetState(size=10))
    fleet_p2: FleetState = field(default_factory=lambda: FleetState(size=10))
    # Attack grids — the only thing AI sees
    attack_p1: AttackGrid = field(default_factory=lambda: AttackGrid(size=10))
    attack_p2: AttackGrid = field(default_factory=lambda: AttackGrid(size=10))
