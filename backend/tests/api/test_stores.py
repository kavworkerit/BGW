import pytest
from uuid import uuid4


class TestStoresAPI:
    """Тесты API для работы с магазинами"""

    def test_create_store(self, client, sample_store):
        """Тест создания магазина"""
        store_data = sample_store.copy()
        store_data["id"] = f"test-store-{uuid4().hex[:8]}"

        response = client.post("/api/stores", json=store_data)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == store_data["id"]
        assert data["name"] == store_data["name"]

    def test_get_stores(self, client, sample_store):
        """Тест получения списка магазинов"""
        # Сначала создадим магазин с уникальным ID
        store_data = sample_store.copy()
        store_data["id"] = f"test-store-{uuid4().hex[:8]}"
        client.post("/api/stores", json=store_data)

        # Теперь получим список
        response = client.get("/api/stores")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(store["id"] == store_data["id"] for store in data)

    def test_get_store_by_id(self, client, sample_store):
        """Тест получения магазина по ID"""
        # Создаем магазин с уникальным ID
        store_data = sample_store.copy()
        store_data["id"] = f"test-store-{uuid4().hex[:8]}"
        client.post("/api/stores", json=store_data)

        # Получаем по ID
        response = client.get(f"/api/stores/{store_data['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == store_data["id"]
        assert data["name"] == store_data["name"]

    def test_get_nonexistent_store(self, client):
        """Тест получения несуществующего магазина"""
        response = client.get("/api/stores/nonexistent")
        assert response.status_code == 404

    def test_create_duplicate_store(self, client, sample_store):
        """Тест создания дубликата магазина"""
        # Создаем уникальные данные для магазина
        store_data = sample_store.copy()
        store_data["id"] = f"test-store-{uuid4().hex[:8]}"

        # Создаем первый магазин
        client.post("/api/stores", json=store_data)

        # Пытаемся создать второй с таким же ID
        response = client.post("/api/stores", json=store_data)
        assert response.status_code == 400  # или другой код ошибки в зависимости от реализации

    def test_store_validation(self, client):
        """Тест валидации данных магазина"""
        invalid_store = {"id": "", "name": ""}  # Пустые поля
        response = client.post("/api/stores", json=invalid_store)
        assert response.status_code == 422