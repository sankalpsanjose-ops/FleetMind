from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.game.models import BoardSize, DifficultyMode
from backend.api.orchestrator import get_orchestrator, AIMode, GameOrchestrator
from backend.db.database import get_db
from backend.db.repository import MatchRepository

router = APIRouter()

# ── Request / Response models ─────────────────────────────────────────────────

class CreateGameRequest(BaseModel):
    board_size: str = "standard"        # "standard" | "large" | "massive"
    difficulty: str = "commander"
    player1_type: str = "human"         # "human" | "ai"
    player2_type: str = "ai"
    ai_provider_1: str | None = None    # "openai" | "anthropic"
    ai_mode_1: str | None = None        # "pure" | "ml"
    ai_model_1: str | None = None       # specific model ID
    ai_provider_2: str | None = "anthropic"
    ai_mode_2: str | None = "pure"
    ai_model_2: str | None = None
    show_reasoning: bool = False

class ShipPlacement(BaseModel):
    ship_type: str
    orientation: str
    row: int
    col: int

class PlaceFleetRequest(BaseModel):
    ships: list[ShipPlacement]

class FireRequest(BaseModel):
    row: int
    col: int

# ── Helpers ───────────────────────────────────────────────────────────────────

BOARD_SIZE_MAP = {
    "standard": BoardSize.STANDARD,
    "large":    BoardSize.LARGE,
    "massive":  BoardSize.MASSIVE,
}

DIFFICULTY_MAP = {d.value: d for d in DifficultyMode}

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/games")
async def create_game(
    req: CreateGameRequest,
    orchestrator: GameOrchestrator = Depends(get_orchestrator),
    db: Session = Depends(get_db),
):
    board_size = BOARD_SIZE_MAP.get(req.board_size)
    if not board_size:
        raise HTTPException(400, f"Invalid board_size: {req.board_size!r}")

    difficulty = DIFFICULTY_MAP.get(req.difficulty)
    if not difficulty:
        raise HTTPException(400, f"Invalid difficulty: {req.difficulty!r}")

    ai_mode_1 = AIMode(req.ai_mode_1) if req.ai_mode_1 else None
    ai_mode_2 = AIMode(req.ai_mode_2) if req.ai_mode_2 else None

    session = await orchestrator.create_session(
        board_size=board_size,
        difficulty=difficulty,
        player1_type=req.player1_type,
        player2_type=req.player2_type,
        ai_provider_1=req.ai_provider_1,
        ai_mode_1=ai_mode_1,
        ai_model_1=req.ai_model_1,
        ai_provider_2=req.ai_provider_2,
        ai_mode_2=ai_mode_2,
        ai_model_2=req.ai_model_2,
        show_reasoning=req.show_reasoning,
    )

    # Record match in DB
    repo = MatchRepository(db)
    match_id = repo.create_match(
        board_size=board_size.value,
        difficulty=req.difficulty,
        player_type=req.player1_type,
        ai_provider_1=req.ai_provider_1,
        ai_mode_1=req.ai_mode_1,
        ai_provider_2=req.ai_provider_2,
        ai_mode_2=req.ai_mode_2,
    )
    session.match_id = match_id

    return {
        "game_id": session.game_id,
        "match_id": match_id,
        "phase": session.engine.state.phase.value,
        "board_size": board_size.value,
        "difficulty": req.difficulty,
    }


@router.post("/games/{game_id}/placement")
async def place_fleet(
    game_id: str,
    req: PlaceFleetRequest,
    orchestrator: GameOrchestrator = Depends(get_orchestrator),
    db: Session = Depends(get_db),
):
    try:
        session = orchestrator.get_session(game_id)
    except KeyError:
        raise HTTPException(404, "Game not found")

    try:
        ships_dicts = [s.model_dump() for s in req.ships]
        await orchestrator.place_human_fleet(game_id, ships_dicts)
    except Exception as e:
        raise HTTPException(400, str(e))

    # Record placements in DB for War Veteran bias learning
    if session.match_id:
        repo = MatchRepository(db)
        for s in req.ships:
            repo.record_placement(
                match_id=session.match_id,
                side="player1",
                ship_type=s.ship_type,
                orientation=s.orientation,
                start_coordinate=f"{s.row},{s.col}",
            )

    return {
        "phase": session.engine.state.phase.value,
        "message": "Fleet placed. Battle begins!" if session.engine.state.phase.value == "battle" else "Fleet placed.",
    }


@router.post("/games/{game_id}/fire")
async def fire(
    game_id: str,
    req: FireRequest,
    orchestrator: GameOrchestrator = Depends(get_orchestrator),
    db: Session = Depends(get_db),
):
    try:
        session = orchestrator.get_session(game_id)
    except KeyError:
        raise HTTPException(404, "Game not found")

    try:
        event = await orchestrator.human_fire(game_id, req.row, req.col)
    except Exception as e:
        raise HTTPException(400, str(e))

    # Record human shot in DB (AI counter-shot is recorded by orchestrator)
    if session.match_id:
        repo = MatchRepository(db)
        repo.record_shot(
            match_id=session.match_id,
            turn=event.get("turn_number", session.engine.state.turn_number),
            side="player1",
            coordinate=f"{req.row},{req.col}",
            result=event["result"],
            ship_type_sunk=event.get("ship_type"),
            reasoning=None,
        )

    return event


@router.get("/games/{game_id}/state")
def get_state(
    game_id: str,
    orchestrator: GameOrchestrator = Depends(get_orchestrator),
):
    try:
        return orchestrator.get_state(game_id)
    except KeyError:
        raise HTTPException(404, "Game not found")


@router.get("/matches")
def list_matches(db: Session = Depends(get_db)):
    repo = MatchRepository(db)
    matches = db.query(__import__("backend.db.models", fromlist=["Match"]).Match).order_by(
        __import__("backend.db.models", fromlist=["Match"]).Match.created_at.desc()
    ).limit(50).all()
    return [
        {
            "id": m.id,
            "board_size": m.board_size,
            "difficulty": m.difficulty,
            "ai_provider_1": m.ai_provider_1,
            "ai_provider_2": m.ai_provider_2,
            "winner": m.winner,
            "total_turns": m.total_turns,
            "created_at": str(m.created_at),
        }
        for m in matches
    ]


@router.get("/matches/win-rates")
def win_rates(db: Session = Depends(get_db)):
    repo = MatchRepository(db)
    return repo.get_win_rates()
