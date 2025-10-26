from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List


class WebPushKeys(BaseModel):
    """Ключи для Web Push подписки."""
    p256dh: str
    auth: str


class WebPushSubscriptionCreate(BaseModel):
    """Данные для создания Web Push подписки."""
    endpoint: str
    keys: WebPushKeys
    user_agent: str

    @validator('endpoint')
    def validate_endpoint(cls, v):
        if not v or not v.startswith('https://'):
            raise ValueError('Invalid endpoint URL')
        return v

    @validator('keys')
    def validate_keys(cls, v):
        if not v.p256dh or not v.auth:
            raise ValueError('Keys must include both p256dh and auth')
        return v


class WebPushSubscriptionResponse(BaseModel):
    """Ответ на подписку."""
    id: str
    status: str


class WebPushTestPayload(BaseModel):
    """Payload для тестового уведомления."""
    title: str = "Тестовое уведомление"
    body: str = "Это тестовое Web Push уведомление"
    icon: Optional[str] = None
    badge: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    require_interaction: bool = False


class WebPushNotificationSend(BaseModel):
    """Запрос на отправку уведомления."""
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    image: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, str]]] = None
    url: Optional[str] = None
    tag: Optional[str] = None
    require_interaction: bool = False
    silent: bool = False
    ttl: int = 86400  # 24 часа


class WebPushSubscriptionInfo(BaseModel):
    """Информация о подписке."""
    id: str
    user_agent: str
    endpoint: str
    ip_address: Optional[str]
    created_at: str
    last_used_at: Optional[str]
    is_active: bool