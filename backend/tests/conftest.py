import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, Column
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.sqlite import BLOB

from app.main import app
from app.core.database import get_db
from app.models.base import Base
import uuid


# Тестовая база данных SQLite в памяти с поддержкой UUID
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Создаем совместимость UUID для SQLite
from sqlalchemy import event
from sqlalchemy.types import TypeDecorator
import uuid

class SQLiteUUID(TypeDecorator):
    """Платформо-независительный UUID тип для SQLite"""
    impl = BLOB
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.bytes

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(bytes=value)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(BLOB())
        return dialect.type_descriptor(String(32))

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Устанавливаем настройки SQLite для тестов"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Переопределение зависимости для тестов"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def db():
    """Фикстура для тестовой базы данных"""
    # Заменяем UUID на SQLite-совместимый тип для тестов
    from app.models.base import UUIDMixin
    original_column = UUIDMixin.id

    # Временно заменяем UUID колонку на BLOB для SQLite
    UUIDMixin.id = Column(BLOB, primary_key=True, default=lambda: uuid.uuid4().bytes)

    try:
        Base.metadata.create_all(bind=engine)
        yield
    finally:
        Base.metadata.drop_all(bind=engine)
        # Восстанавливаем оригинальную колонку
        UUIDMixin.id = original_column


@pytest.fixture
def client(db):
    """Фикстура для тестового клиента"""
    yield TestClient(app)


@pytest.fixture
def sample_game():
    """Фикстура с примером игры"""
    return {
        "title": "Громкое дело",
        "synonyms": ["Громкое дело: Новая эра"],
        "bgg_id": "12345",
        "publisher": "Правильные игры",
        "tags": ["детектив", "расследование"]
    }


@pytest.fixture
def sample_store():
    """Фикстура с примером магазина"""
    return {
        "id": "hobbygames",
        "name": "Hobby Games",
        "site_url": "https://hobbygames.ru",
        "region": "RU",
        "currency": "RUB"
    }