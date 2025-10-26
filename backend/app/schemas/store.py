from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StoreBase(BaseModel):
    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    site_url: Optional[str] = None
    region: str = "RU"
    currency: str = "RUB"


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    site_url: Optional[str] = None
    region: Optional[str] = None
    currency: Optional[str] = None


class Store(StoreBase):
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True