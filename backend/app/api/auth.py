from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Простая аутентификация для локального использования."""
    # В локальной версии используем простую проверку
    # В продакшене здесь должна быть реальная аутентификация
    if request.username == "admin" and request.password == "admin":
        return {
            "access_token": "local-dev-token",
            "token_type": "bearer"
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(token: str = Depends(security)):
    """Получение текущего пользователя (упрощенная версия)."""
    if token.credentials == "local-dev-token":
        return {"username": "admin"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )