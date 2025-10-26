from sqlalchemy import Column, String, DateTime, Text, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy_utils import JSONType
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid

class Game(BaseModel):
    __tablename__ = "game"

    title = Column(String(500), nullable=False, index=True)
    # Используем JSONType для кросс-базовой совместимости
    synonyms = Column(JSONType, default=list)
    bgg_id = Column(String(50), unique=True, nullable=True, index=True)
    publisher = Column(String(200), nullable=True, index=True)
    tags = Column(JSONType, default=list)
    description = Column(Text, nullable=True)
    min_players = Column(Integer, nullable=True)
    max_players = Column(Integer, nullable=True)
    min_playtime = Column(Integer, nullable=True)  # минут
    max_playtime = Column(Integer, nullable=True)  # минут
    year_published = Column(Integer, nullable=True)
    language = Column(String(10), default="RU")  # RU, EN, etc.
    complexity = Column(Float, nullable=True)  # 1-5
    image_url = Column(String(500), nullable=True)
    rating_bgg = Column(Float, nullable=True)  # рейтинг BGG
    rating_users = Column(Float, nullable=True)  # пользовательский рейтинг
    weight = Column(Float, nullable=True)  # вес/сложность

    # Relationships
    listing_events = relationship("ListingEvent", back_populates="game")
    price_history = relationship("PriceHistory", back_populates="game")

    def __repr__(self):
        return f"Game(id={self.id}, title='{self.title}')"

    def __str__(self):
        return self.title