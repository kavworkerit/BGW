def test_root_endpoint(client):
    """Тест корневого эндпоинта"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Мониторинг настольных игр API"
    assert data["version"] == "1.0.0"


def test_health_check(client):
    """Тест проверки здоровья"""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "board-games-monitor"


def test_metrics_endpoint(client):
    """Тест эндпоинта метрик"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]