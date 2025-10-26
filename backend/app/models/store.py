from sqlalchemy import Column, String
from .base import BaseModel


class Store(BaseModel):
    __tablename__ = "store"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    site_url = Column(String(500), nullable=True)
    region = Column(String(10), default="RU")
    currency = Column(String(3), default="RUB")

    def __repr__(self):
        return f"<Store(id='{self.id}', name='{self.name}')>"