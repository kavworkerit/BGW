from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.crud.base import CRUDBase
from app.models.game import Game
from app.schemas.game import GameCreate, GameUpdate


class CRUDGame(CRUDBase[Game, GameCreate, GameUpdate]):
    def search(self, db: Session, query: str, *, skip: int = 0, limit: int = 100):
        """Поиск игр по названию и синонимам."""
        search_filter = or_(
            Game.title.ilike(f"%{query}%"),
            Game.synonyms.any(query)
        )
        return db.query(self.model).filter(search_filter).offset(skip).limit(limit).all()

    def get_by_bgg_id(self, db: Session, bgg_id: str):
        """Получить игру по BGG ID."""
        return db.query(self.model).filter(Game.bgg_id == bgg_id).first()


game_crud = CRUDGame(Game)