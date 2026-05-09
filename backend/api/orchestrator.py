from __future__ import annotations
import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Awaitable

from backend.game.models import (
    BoardSize, DifficultyMode, Coordinate, Orientation, ShipType,
    GamePhase, CellState
)
from backend.game.engine import GameEngine
from backend.game.fleet import FleetManager, FLEET_CONFIG
from backend.ai.provider import GameContext, get_provider
import backend.ai.openai_provider      # noqa: F401 — registers "openai"
import backend.ai.anthropic_provider   # noqa: F401 — registers "anthropic"
from backend.ml.heatmap import ProbabilityHeatmap
from backend.ml.qlearning import QLearningAgent
from backend.ml.trainer import get_agent

# Difficulty → (heatmap_weight, rl_weight)
ML_WEIGHTS: dict[DifficultyMode, tuple[float, float]] = {
    DifficultyMode.CADET:       (0.0, 0.0),
    DifficultyMode.COMMANDER:   (1.0, 0.0),
    DifficultyMode.ADMIRAL:     (0.8, 0.2),
    DifficultyMode.WAR_VETERAN: (0.6, 0.4),
    DifficultyMode.BLACK_OPS:   (0.3, 0.7),
    DifficultyMode.ARMADA:      (0.8, 0.2),
    DifficultyMode.GUERRILLA:   (1.0, 0.0),
}

DIFFICULTY_REQUIRES_GAP = {
    DifficultyMode.ADMIRAL, DifficultyMode.WAR_VETERAN,
    DifficultyMode.BLACK_OPS, DifficultyMode.GUERRILLA,
}

class AIMode(str, Enum):
    PURE = "pure"
    ML   = "ml"

@dataclass
class PlayerConfig:
    player_type: str        # "human" | "ai"
    provider_name: str | None = None
    ai_mode: AIMode | None = None

@dataclass
class GameSession:
    game_id: str
    engine: GameEngine
    board_size: BoardSize
    difficulty: DifficultyMode
    player1: PlayerConfig
    player2: PlayerConfig
    match_id: int | None = None
    start_time: float = field(default_factory=time.time)
    # Per-side ML state
    heatmap_p1: ProbabilityHeatmap | None = None
    heatmap_p2: ProbabilityHeatmap | None = None
    # Event callbacks registered by WebSocket handler
    _event_callbacks: list[Callable] = field(default_factory=list)

    def register_event_callback(self, cb: Callable[[dict], Awaitable[None]]) -> None:
        self._event_callbacks.append(cb)

    async def emit(self, event: dict) -> None:
        for cb in self._event_callbacks:
            try:
                await cb(event)
            except Exception:
                pass  # Don't let broken WS connections kill the game

class GameOrchestrator:
    def __init__(self):
        self._sessions: dict[str, GameSession] = {}

    def _remaining_ship_sizes(self, engine: GameEngine, enemy_side: str) -> list[int]:
        fleet = engine.state.fleet_p2 if enemy_side == "player2" else engine.state.fleet_p1
        return [s.size for s in fleet.ships if not s.sunk]

    def _make_heatmap(self, difficulty: DifficultyMode, board_size: BoardSize) -> ProbabilityHeatmap:
        ships = [s.size for s in FLEET_CONFIG[difficulty][board_size]]
        return ProbabilityHeatmap(board_size=board_size.value, remaining_ships=ships)

    async def create_session(
        self,
        board_size: BoardSize,
        difficulty: DifficultyMode,
        player1_type: str,
        player2_type: str,
        ai_provider_1: str | None,
        ai_mode_1: AIMode | None,
        ai_provider_2: str | None,
        ai_mode_2: AIMode | None,
    ) -> GameSession:
        game_id = str(uuid.uuid4())
        engine = GameEngine(board_size, difficulty, player1_type, player2_type)
        engine.transition_to_placement()

        p1 = PlayerConfig(player1_type, ai_provider_1, ai_mode_1)
        p2 = PlayerConfig(player2_type, ai_provider_2, ai_mode_2)

        session = GameSession(
            game_id=game_id,
            engine=engine,
            board_size=board_size,
            difficulty=difficulty,
            player1=p1,
            player2=p2,
        )

        # Initialize ML heatmaps for sides that use them
        hw, _ = ML_WEIGHTS[difficulty]
        if hw > 0:
            session.heatmap_p1 = self._make_heatmap(difficulty, board_size)
            session.heatmap_p2 = self._make_heatmap(difficulty, board_size)

        require_gap = difficulty in DIFFICULTY_REQUIRES_GAP
        manager = FleetManager(board_size=board_size.value, require_gap=require_gap)

        # Auto-place AI fleets
        if player1_type == "ai":
            fleet = manager.place_fleet_random(difficulty, board_size)
            engine.set_fleet("player1", fleet)
        if player2_type == "ai":
            fleet = manager.place_fleet_random(difficulty, board_size)
            engine.set_fleet("player2", fleet)

        # If both sides are AI, start battle immediately
        if player1_type == "ai" and player2_type == "ai":
            engine.start_battle()

        self._sessions[game_id] = session
        return session

    def get_session(self, game_id: str) -> GameSession:
        if game_id not in self._sessions:
            raise KeyError(f"No session for game_id={game_id!r}")
        return self._sessions[game_id]

    async def place_human_fleet(self, game_id: str, ships: list[dict]) -> None:
        session = self.get_session(game_id)
        from backend.game.models import FleetState, Ship
        fleet = FleetState(size=session.board_size.value)
        manager = FleetManager(
            board_size=session.board_size.value,
            require_gap=session.difficulty in DIFFICULTY_REQUIRES_GAP
        )
        for s in ships:
            ship = Ship(
                ship_type=ShipType(s["ship_type"]),
                orientation=Orientation(s["orientation"]),
                bow=Coordinate(s["row"], s["col"]),
            )
            manager.place_ship(fleet, ship)
        # Determine which side is human
        side = "player1" if session.player1.player_type == "human" else "player2"
        session.engine.set_fleet(side, fleet)
        # Start battle once both sides have fleets
        if session.engine._fleets_ready["player1"] and session.engine._fleets_ready["player2"]:
            session.engine.start_battle()

    def _build_candidates(
        self,
        session: GameSession,
        shooter: str,
        ai_mode: AIMode,
    ) -> list[Coordinate] | None:
        """Build ML candidate list for AI+ML mode."""
        hw, rw = ML_WEIGHTS[session.difficulty]
        if ai_mode != AIMode.ML or (hw == 0 and rw == 0):
            return None

        attack_grid = session.engine.get_attack_grid_for_ai(shooter)
        heatmap = session.heatmap_p1 if shooter == "player1" else session.heatmap_p2

        import numpy as np
        size = session.board_size.value
        scores: dict[Coordinate, float] = {}

        if heatmap and hw > 0:
            hm_scores = heatmap.score_cells(attack_grid)
            max_hm = max(hm_scores.values()) if hm_scores else 1.0
            for coord, s in hm_scores.items():
                scores[coord] = scores.get(coord, 0.0) + hw * (s / max_hm)

        if rw > 0:
            rl_agent = get_agent(size)
            unknown = attack_grid.unknown_cells()
            rl_scores = {c: rl_agent._get_q(attack_grid, c) for c in unknown}
            max_rl = max(rl_scores.values()) if rl_scores else 1.0
            if max_rl == 0:
                max_rl = 1.0
            for coord, s in rl_scores.items():
                scores[coord] = scores.get(coord, 0.0) + rw * (s / max_rl)

        return sorted(scores, key=lambda c: scores[c], reverse=True)[:5] if scores else None

    async def _run_ai_turn(self, session: GameSession, shooter: str) -> dict:
        """Execute one AI turn. Returns shot event dict."""
        config = session.player1 if shooter == "player1" else session.player2
        attack_grid = session.engine.get_attack_grid_for_ai(shooter)

        await session.emit({"type": "ai_thinking", "side": shooter,
                            "turn": session.engine.state.turn_number})

        candidates = self._build_candidates(session, shooter, config.ai_mode)
        ctx = GameContext(
            board_size=session.board_size.value,
            difficulty=session.difficulty,
            remaining_ship_sizes=self._remaining_ship_sizes(
                session.engine,
                "player2" if shooter == "player1" else "player1"
            ),
            turn_number=session.engine.state.turn_number,
            show_reasoning=False,
        )

        provider = get_provider(config.provider_name)
        decision = await provider.decide_move(attack_grid, ctx, candidates)

        # Ensure the coordinate is unknown (safety fallback)
        coord = decision.coordinate
        if attack_grid.get(coord) != CellState.UNKNOWN:
            unknown = attack_grid.unknown_cells()
            coord = unknown[0] if unknown else coord

        shot_event = session.engine.fire(shooter, coord)

        # Update ML state
        heatmap = session.heatmap_p1 if shooter == "player1" else session.heatmap_p2
        if heatmap:
            heatmap.update(coord, shot_event.result)

        event = {
            "type": "shot_fired",
            "side": shooter,
            "row": coord.row,
            "col": coord.col,
            "result": shot_event.result,
            "ship_type": shot_event.ship_type,
            "reasoning": decision.reasoning,
        }
        await session.emit(event)

        if shot_event.result == "sunk":
            await session.emit({"type": "ship_sunk", "side": shooter,
                                "ship_type": shot_event.ship_type})

        if session.engine.state.phase == GamePhase.GAME_OVER:
            await session.emit({"type": "game_over", "winner": session.engine.state.winner,
                                "total_turns": session.engine.state.turn_number})

        return event

    async def human_fire(self, game_id: str, row: int, col: int) -> dict:
        """Process a human shot, then trigger AI response turn."""
        session = self.get_session(game_id)
        coord = Coordinate(row, col)
        shot_event = session.engine.fire("player1", coord)

        heatmap = session.heatmap_p1
        if heatmap:
            heatmap.update(coord, shot_event.result)

        event = {
            "type": "shot_fired",
            "side": "player1",
            "row": coord.row,
            "col": coord.col,
            "result": shot_event.result,
            "ship_type": shot_event.ship_type,
            "reasoning": None,
        }
        await session.emit(event)

        if session.engine.state.phase == GamePhase.GAME_OVER:
            await session.emit({"type": "game_over", "winner": session.engine.state.winner,
                                "total_turns": session.engine.state.turn_number})
            return event

        # Trigger AI counter-turn
        if session.engine.state.current_turn == "player2" and session.player2.player_type == "ai":
            await self._run_ai_turn(session, "player2")

        return event

    async def run_ai_vs_ai(self, game_id: str) -> None:
        """Run a full AI vs AI game, emitting events along the way."""
        session = self.get_session(game_id)
        while session.engine.state.phase == GamePhase.BATTLE:
            current = session.engine.state.current_turn
            await self._run_ai_turn(session, current)

    def get_state(self, game_id: str) -> dict:
        session = self.get_session(game_id)
        engine = session.engine
        size = session.board_size.value

        def serialize_grid(grid):
            return {
                f"{r},{c}": engine.state.attack_p1.get(Coordinate(r, c)).value
                if grid == "p1" else
                engine.state.attack_p2.get(Coordinate(r, c)).value
                for r in range(size) for c in range(size)
            }

        return {
            "game_id": game_id,
            "phase": engine.state.phase.value,
            "current_turn": engine.state.current_turn,
            "turn_number": engine.state.turn_number,
            "winner": engine.state.winner,
            "attack_grid": {
                "player1": serialize_grid("p1"),
                "player2": serialize_grid("p2"),
            },
        }

# Global orchestrator instance
_orchestrator: GameOrchestrator | None = None

def get_orchestrator() -> GameOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = GameOrchestrator()
    return _orchestrator
