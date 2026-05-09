import pytest
from backend.game.models import (
    Coordinate, Orientation, ShipType, Ship, FleetState,
    BoardSize, DifficultyMode, GamePhase, CellState
)
from backend.game.engine import GameEngine, InvalidMoveError
from backend.game.fleet import FleetManager

def make_engine(board_size=BoardSize.STANDARD, difficulty=DifficultyMode.COMMANDER):
    engine = GameEngine(
        board_size=board_size,
        difficulty=difficulty,
        player1_type="human",
        player2_type="ai"
    )
    engine.transition_to_placement()
    return engine

def place_minimal_fleet(engine, side):
    """Place one patrol boat — quick to sink in tests."""
    fleet = FleetState(size=10)
    ship = Ship(ShipType.PATROL, Orientation.HORIZONTAL, Coordinate(0, 0))
    fleet.ships.append(ship)
    engine.set_fleet(side, fleet)

def test_initial_phase_is_setup():
    engine = GameEngine(BoardSize.STANDARD, DifficultyMode.COMMANDER, "human", "ai")
    assert engine.state.phase == GamePhase.SETUP

def test_transitions_to_placement():
    engine = make_engine()
    assert engine.state.phase == GamePhase.PLACEMENT

def test_transitions_to_battle_after_both_fleets_placed():
    engine = make_engine()
    place_minimal_fleet(engine, "player1")
    place_minimal_fleet(engine, "player2")
    engine.start_battle()
    assert engine.state.phase == GamePhase.BATTLE

def test_fire_hit_registers_correctly():
    engine = make_engine()
    place_minimal_fleet(engine, "player1")
    place_minimal_fleet(engine, "player2")
    engine.start_battle()
    event = engine.fire("player1", Coordinate(0, 0))
    assert event.result in ("hit", "sunk")
    assert engine.state.attack_p1.get(Coordinate(0, 0)) in (CellState.HIT, CellState.SUNK)

def test_fire_miss_registers_correctly():
    engine = make_engine()
    place_minimal_fleet(engine, "player1")
    place_minimal_fleet(engine, "player2")
    engine.start_battle()
    event = engine.fire("player1", Coordinate(5, 5))
    assert event.result == "miss"
    assert engine.state.attack_p1.get(Coordinate(5, 5)) == CellState.MISS

def test_repeat_shot_rejected():
    engine = make_engine()
    place_minimal_fleet(engine, "player1")
    place_minimal_fleet(engine, "player2")
    engine.start_battle()
    engine.fire("player1", Coordinate(0, 0))
    engine.fire("player2", Coordinate(9, 9))
    with pytest.raises(InvalidMoveError, match="already fired"):
        engine.fire("player1", Coordinate(0, 0))

def test_wrong_turn_rejected():
    engine = make_engine()
    place_minimal_fleet(engine, "player1")
    place_minimal_fleet(engine, "player2")
    engine.start_battle()
    with pytest.raises(InvalidMoveError, match="not your turn"):
        engine.fire("player2", Coordinate(0, 0))

def test_fleet_state_never_in_attack_grid():
    """Anti-cheat: fleet positions never bleed into attack grid."""
    engine = make_engine()
    place_minimal_fleet(engine, "player1")
    place_minimal_fleet(engine, "player2")
    engine.start_battle()
    assert not hasattr(engine.state.attack_p1, 'ships')
    assert not hasattr(engine.state.attack_p2, 'ships')

def test_game_over_when_all_ships_sunk():
    engine = make_engine()
    place_minimal_fleet(engine, "player1")
    place_minimal_fleet(engine, "player2")
    engine.start_battle()
    # Patrol boat occupies (0,0) and (0,1) — sink it
    engine.fire("player1", Coordinate(0, 0))
    engine.fire("player2", Coordinate(9, 9))  # p2 misses
    engine.fire("player1", Coordinate(0, 1))
    assert engine.state.phase == GamePhase.GAME_OVER
    assert engine.state.winner == "player1"

def test_get_attack_grid_for_ai_excludes_fleet():
    engine = make_engine()
    place_minimal_fleet(engine, "player1")
    place_minimal_fleet(engine, "player2")
    engine.start_battle()
    grid = engine.get_attack_grid_for_ai("player2")
    assert not hasattr(grid, 'ships')
    assert not hasattr(grid, 'fleet')
