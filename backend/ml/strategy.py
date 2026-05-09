from __future__ import annotations
from abc import ABC, abstractmethod
from backend.game.models import AttackGrid, Coordinate

class MLStrategy(ABC):
    """Pluggable ML strategy interface. Swap implementations without touching game engine."""

    @abstractmethod
    def score_cells(self, attack_grid: AttackGrid) -> dict[Coordinate, float]:
        """Score every unknown cell. Higher score = better target."""
        ...

    @abstractmethod
    def top_candidates(self, attack_grid: AttackGrid, n: int) -> list[Coordinate]:
        """Return the top-n candidate coordinates, sorted best-first."""
        ...

    @abstractmethod
    def update(self, coord: Coordinate, result: str) -> None:
        """Update strategy state after a shot result ('hit', 'miss', 'sunk')."""
        ...
