from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class GameBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    synonyms: List[str] = []
    bgg_id: Optional[str] = None
    publisher: Optional[str] = None
    tags: List[str] = []


class GameCreate(GameBase):
    pass


class GameUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    synonyms: Optional[List[str]] = None
    bgg_id: Optional[str] = None
    publisher: Optional[str] = None
    tags: Optional[List[str]] = None


class Game(GameBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True