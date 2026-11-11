from __future__ import annotations

def test_health(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_dictionaries_skills(client):
    r = client.get("/dictionaries/skills")
    assert r.status_code == 200
    data = r.json()               # список dict'ов
    assert len(data) > 0          # не пустой
    first = data[0]               # первый элемент, это dict
    assert "id" in first          # ключ id есть
    assert "name" in first        # ключ name есть
    assert "matching_with_opportunity" not in first

def test_dictionaries_foo(client):
    response = client.get("/dictionaries/foo")
    assert response.status_code == 422
