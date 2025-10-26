from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.api import auth, games, stores, agents, events, rules, notifications, settings as settings_api
from app.celery_app import celery_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация базы данных
    Base.metadata.create_all(bind=engine)
    yield
    # Очистка при shutdown


app = FastAPI(
    title="Мониторинг настольных игр",
    description="Система мониторинга релизов, предзаказов и скидок настольных игр",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["Аутентификация"])
app.include_router(games.router, prefix="/api/games", tags=["Игры"])
app.include_router(stores.router, prefix="/api/stores", tags=["Магазины"])
app.include_router(agents.router, prefix="/api/agents", tags=["Агенты"])
app.include_router(events.router, prefix="/api/events", tags=["События"])
app.include_router(rules.router, prefix="/api/rules", tags=["Правила"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Уведомления"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["Настройки"])


@app.get("/")
async def root():
    return {"message": "Мониторинг настольных игр API", "version": "1.0.0"}


@app.get("/healthz")
async def health_check():
    return {"status": "ok", "service": "board-games-monitor"}


@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )