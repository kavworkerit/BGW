from sqlalchemy import Column, String, Text, Boolean, Integer, Float
from .base import BaseModel


class Store(BaseModel):
    __tablename__ = "store"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    site_url = Column(String(500), nullable=True)
    region = Column(String(10), default="RU", index=True)
    currency = Column(String(3), default="RUB")
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    working_hours = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0)  # приоритет в поиске
    shipping_info = Column(Text, nullable=True)
    payment_methods = Column(String(500), nullable=True)  # JSON строка с методами оплаты
    social_links = Column(Text, nullable=True)  # JSON строка с соц. сетями

    def __repr__(self):
        return f"<Store(id='{self.id}', name='{self.name}', active={self.is_active})>"