from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.db.database import Base

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    board_size = Column(Integer, nullable=False)
    difficulty = Column(String, nullable=False)
    player_type = Column(String, nullable=False)    # "human" | "ai"
    ai_provider_1 = Column(String)
    ai_mode_1 = Column(String)                      # "pure" | "ml"
    ai_provider_2 = Column(String)
    ai_mode_2 = Column(String)
    winner = Column(String)                          # "player1" | "player2" | None
    total_turns = Column(Integer)
    duration_seconds = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class Shot(Base):
    __tablename__ = "shots"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    side = Column(String, nullable=False)            # "player1" | "player2"
    coordinate = Column(String, nullable=False)      # e.g. "A5"
    result = Column(String, nullable=False)          # "hit" | "miss" | "sunk"
    ship_type_sunk = Column(String)
    reasoning = Column(String)                       # AI reasoning text, if captured
    timestamp = Column(DateTime, server_default=func.now())

class Placement(Base):
    __tablename__ = "placements"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    side = Column(String, nullable=False)
    ship_type = Column(String, nullable=False)
    orientation = Column(String, nullable=False)
    start_coordinate = Column(String, nullable=False)   # e.g. "A0"
