from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from backend.game.models import Coordinate, AttackGrid, DifficultyMode

@dataclass
class GameContext:
    """Everything the AI needs to know — no fleet positions."""
    board_size: int
    difficulty: DifficultyMode
    remaining_ship_sizes: list[int]     # sizes of enemy ships still alive (not positions)
    turn_number: int
    show_reasoning: bool = False

@dataclass
class MoveDecision:
    coordinate: Coordinate
    reasoning: str | None = None

class AIProvider(ABC):
    """
    Provider-agnostic interface. Add new models (Gemini, Grok, etc.)
    by subclassing this and registering in the provider registry.
    """
    name: str = "base"

    @abstractmethod
    async def decide_move(
        self,
        attack_grid: AttackGrid,
        context: GameContext,
        candidates: list[Coordinate] | None = None,
    ) -> MoveDecision:
        """
        attack_grid: only hits/misses/unknown — never fleet positions.
        candidates: optional top-N from ML engine (AI+ML mode).
        """
        ...

# Provider registry — add entries here to make new models available
_REGISTRY: dict[str, type[AIProvider]] = {}

def register_provider(cls: type[AIProvider]) -> type[AIProvider]:
    _REGISTRY[cls.name] = cls
    return cls

def get_provider(name: str, model: str | None = None) -> AIProvider:
    if name not in _REGISTRY:
        raise ValueError(f"Unknown AI provider: {name!r}. Available: {list(_REGISTRY)}")
    return _REGISTRY[name](model=model)
