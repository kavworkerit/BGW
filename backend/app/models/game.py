from sqlalchemy import Column, String, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel


class Game(BaseModel):
    __tablename__ = "game"

    title = Column(String(500), nullable=False, index=True)
    synonyms = Column(ARRAY(String), default=[])
    bgg_id = Column(String(50), unique=True, nullable=True)
    publisher = Column(String(200), nullable=True)
    tags = Column(ARRAY(String), default=[])

    def __repr__(self):
        return f"<Game(title='{self.title}')>"