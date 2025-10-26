from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class WebPushSubscription(Base):
    """Модель для подписок Web Push."""
    __tablename__ = "webpush_subscription"

    id = Column(String, primary_key=True)  # UUID или уникальный хэш
    user_agent = Column(String(500), nullable=False)
    endpoint = Column(String(1000), nullable=False, unique=True)
    p256dh_key = Column(String(255), nullable=False)
    auth_key = Column(String(255), nullable=False)

    # Метаданные
    ip_address = Column(String(45))  # IPv6 compatible
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)

    # Дополнительные данные (например, preferences)
    data = Column(JSON, default={})

    def __repr__(self):
        return f"<WebPushSubscription(id={self.id}, endpoint={self.endpoint[:50]}...)>"

    @property
    def subscription_info(self) -> dict:
        """Возвращает информацию о подписке в формате pywebpush."""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh_key,
                "auth": self.auth_key
            }
        }