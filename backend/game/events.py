from dataclasses import dataclass
from backend.game.models import Coordinate

@dataclass
class ShotEvent:
    turn: str               # "player1" | "player2"
    coordinate: Coordinate
    result: str             # "hit" | "miss" | "sunk"
    ship_type: str | None = None    # set when result == "sunk"
    reasoning: str | None = None    # AI reasoning text, if enabled
