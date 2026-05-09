import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.database import Base
from backend.db.models import Match, Shot, Placement
from backend.db.repository import MatchRepository

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()

def test_create_and_retrieve_match(session):
    repo = MatchRepository(session)
    match_id = repo.create_match(
        board_size=10, difficulty="commander",
        player_type="human",
        ai_provider_1="anthropic", ai_mode_1="pure",
        ai_provider_2=None, ai_mode_2=None
    )
    match = repo.get_match(match_id)
    assert match.board_size == 10
    assert match.difficulty == "commander"
    assert match.winner is None

def test_record_shot(session):
    repo = MatchRepository(session)
    match_id = repo.create_match(10, "commander", "human", "anthropic", "pure", None, None)
    repo.record_shot(match_id, turn=1, side="player1",
                     coordinate="A1", result="hit", ship_type_sunk=None, reasoning=None)
    shots = repo.get_shots(match_id)
    assert len(shots) == 1
    assert shots[0].result == "hit"

def test_close_match(session):
    repo = MatchRepository(session)
    match_id = repo.create_match(10, "commander", "human", "anthropic", "pure", None, None)
    repo.close_match(match_id, winner="player1", total_turns=42, duration_seconds=120)
    match = repo.get_match(match_id)
    assert match.winner == "player1"
    assert match.total_turns == 42

def test_record_placement(session):
    repo = MatchRepository(session)
    match_id = repo.create_match(10, "commander", "human", "anthropic", "pure", None, None)
    repo.record_placement(match_id, side="player1",
                          ship_type="carrier", orientation="horizontal", start_coordinate="A0")
    placements = repo.get_placements(match_id, side="player1")
    assert len(placements) == 1
    assert placements[0].ship_type == "carrier"

def test_get_win_rates(session):
    repo = MatchRepository(session)
    for winner in ["player1", "player1", "player2"]:
        mid = repo.create_match(10, "commander", "human", "anthropic", "pure", "openai", "pure")
        repo.close_match(mid, winner=winner, total_turns=30, duration_seconds=60)
    rates = repo.get_win_rates()
    assert rates["anthropic"]["wins"] == 2
    assert rates["openai"]["wins"] == 1
