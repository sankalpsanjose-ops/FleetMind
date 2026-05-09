from sqlalchemy.orm import Session
from backend.db.models import Match, Shot, Placement

class MatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_match(self, board_size, difficulty, player_type,
                     ai_provider_1, ai_mode_1, ai_provider_2, ai_mode_2) -> int:
        match = Match(
            board_size=board_size, difficulty=difficulty, player_type=player_type,
            ai_provider_1=ai_provider_1, ai_mode_1=ai_mode_1,
            ai_provider_2=ai_provider_2, ai_mode_2=ai_mode_2,
        )
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        return match.id

    def get_match(self, match_id: int) -> Match:
        return self.db.query(Match).filter(Match.id == match_id).first()

    def close_match(self, match_id: int, winner: str, total_turns: int, duration_seconds: float):
        match = self.get_match(match_id)
        match.winner = winner
        match.total_turns = total_turns
        match.duration_seconds = duration_seconds
        self.db.commit()

    def record_shot(self, match_id, turn, side, coordinate, result, ship_type_sunk, reasoning):
        shot = Shot(
            match_id=match_id, turn_number=turn, side=side,
            coordinate=coordinate, result=result,
            ship_type_sunk=ship_type_sunk, reasoning=reasoning
        )
        self.db.add(shot)
        self.db.commit()

    def get_shots(self, match_id: int) -> list[Shot]:
        return self.db.query(Shot).filter(Shot.match_id == match_id).all()

    def record_placement(self, match_id, side, ship_type, orientation, start_coordinate):
        p = Placement(
            match_id=match_id, side=side, ship_type=ship_type,
            orientation=orientation, start_coordinate=start_coordinate
        )
        self.db.add(p)
        self.db.commit()

    def get_placements(self, match_id: int, side: str) -> list[Placement]:
        return self.db.query(Placement).filter(
            Placement.match_id == match_id, Placement.side == side
        ).all()

    def get_historical_placements(self, side: str) -> list[Placement]:
        """For War Veteran mode: load all historical human placements for bias analysis."""
        return self.db.query(Placement).filter(Placement.side == side).all()

    def get_win_rates(self) -> dict:
        matches = self.db.query(Match).filter(Match.winner.isnot(None)).all()
        rates: dict[str, dict] = {}
        for match in matches:
            for provider, player in [
                (match.ai_provider_1, "player1"),
                (match.ai_provider_2, "player2"),
            ]:
                if provider is None:
                    continue
                if provider not in rates:
                    rates[provider] = {"wins": 0, "losses": 0, "total": 0}
                rates[provider]["total"] += 1
                if match.winner == player:
                    rates[provider]["wins"] += 1
                else:
                    rates[provider]["losses"] += 1
        return rates
