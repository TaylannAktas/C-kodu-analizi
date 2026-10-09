import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_ana_sayfa_200_doner(client):
    assert client.get("/").status_code == 200


def test_health_ok_doner(client):
    yanit = client.get("/health")
    assert yanit.status_code == 200
    assert yanit.get_json()["status"] == "ok"


def test_scan_get_hazir_bilgisi_doner(client):
    yanit = client.get("/api/scan")
    assert yanit.status_code == 200
    assert yanit.get_json()["status"] == "ready"


def test_scan_kod_olmadan_400_doner(client):
    assert client.post("/api/scan", json={}).status_code == 400


def test_scan_zafiyeti_raporlar(client):
    yanit = client.post("/api/scan", json={"code": "gets(buf);"})
    govde = yanit.get_json()

    assert yanit.status_code == 200
    assert govde["status"] == "success"
    assert govde["toplam_zafiyet"] == 1
    assert govde["zafiyetler"][0]["fonksiyon"] == "gets"
    assert govde["fonksiyon_durumlari"]["gets"]["durum"] == "zafiyetli"
