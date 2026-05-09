from __future__ import annotations
from backend.game.models import (
    GameState, GamePhase, FleetState, AttackGrid,
    CellState, Coordinate, BoardSize, DifficultyMode
)
from backend.game.events import ShotEvent

class InvalidMoveError(ValueError):
    pass

class GameEngine:
    def __init__(
        self,
        board_size: BoardSize,
        difficulty: DifficultyMode,
        player1_type: str,  # "human" | "ai"
        player2_type: str,
    ):
        self.board_size = board_size
        self.difficulty = difficulty
        self.player1_type = player1_type
        self.player2_type = player2_type
        self.state = GameState(
            board_size=board_size.value,
            difficulty=difficulty,
            fleet_p1=FleetState(size=board_size.value),
            fleet_p2=FleetState(size=board_size.value),
            attack_p1=AttackGrid(size=board_size.value),
            attack_p2=AttackGrid(size=board_size.value),
        )
        self._fleets_ready = {"player1": False, "player2": False}

    def transition_to_placement(self) -> None:
        assert self.state.phase == GamePhase.SETUP
        self.state.phase = GamePhase.PLACEMENT

    def set_fleet(self, side: str, fleet: FleetState) -> None:
        assert self.state.phase == GamePhase.PLACEMENT, "Can only set fleet during placement"
        assert side in ("player1", "player2")
        if side == "player1":
            self.state.fleet_p1 = fleet
        else:
            self.state.fleet_p2 = fleet
        self._fleets_ready[side] = True

    def start_battle(self) -> None:
        assert self._fleets_ready["player1"] and self._fleets_ready["player2"], \
            "Both fleets must be placed before battle"
        self.state.phase = GamePhase.BATTLE
        self.state.current_turn = "player1"

    def fire(self, shooter: str, coord: Coordinate) -> ShotEvent:
        if self.state.phase != GamePhase.BATTLE:
            raise InvalidMoveError("Game is not in battle phase")
        if self.state.current_turn != shooter:
            raise InvalidMoveError(f"not your turn — it is {self.state.current_turn}'s turn")
        if not coord.is_valid(self.state.board_size):
            raise InvalidMoveError(f"Coordinate {coord} out of bounds")

        if shooter == "player1":
            attack_grid = self.state.attack_p1
            enemy_fleet = self.state.fleet_p2
            next_turn = "player2"
        else:
            attack_grid = self.state.attack_p2
            enemy_fleet = self.state.fleet_p1
            next_turn = "player1"

        if attack_grid.get(coord) != CellState.UNKNOWN:
            raise InvalidMoveError(f"already fired at {coord}")

        ship = enemy_fleet.ship_at(coord)
        if ship is None:
            attack_grid.set(coord, CellState.MISS)
            event = ShotEvent(turn=shooter, coordinate=coord, result="miss")
        else:
            ship.register_hit(coord)
            if ship.sunk:
                for cell in ship.occupied_cells():
                    attack_grid.set(cell, CellState.SUNK)
                event = ShotEvent(
                    turn=shooter, coordinate=coord,
                    result="sunk", ship_type=ship.ship_type.value
                )
            else:
                attack_grid.set(coord, CellState.HIT)
                event = ShotEvent(turn=shooter, coordinate=coord, result="hit")

        self.state.turn_number += 1

        if enemy_fleet.all_sunk():
            self.state.phase = GamePhase.GAME_OVER
            self.state.winner = shooter
        else:
            self.state.current_turn = next_turn

        return event

    def get_attack_grid_for_ai(self, side: str) -> AttackGrid:
        """Returns only the attack grid for the given side — never fleet positions."""
        return self.state.attack_p1 if side == "player1" else self.state.attack_p2
