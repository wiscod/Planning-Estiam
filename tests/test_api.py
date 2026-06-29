"""Tests unitaires pour les endpoints FastAPI."""

import json
import pytest
from fastapi.testclient import TestClient

import api

SAMPLE_PLANNING = {
    "timestamp": "2026-07-01T12:00:00",
    "weeks": {
        "27": {
            "semaine": 27,
            "courses": [
                {"date": "30 june", "time": "09:30", "matiere": "Hackathon"},
                {"date": "01 july", "time": "14:00", "matiere": "Hackathon"},
            ],
        },
        "28": {
            "semaine": 28,
            "courses": [
                {"date": "07 july", "time": "09:30 (Distanciel)", "matiere": "ISM"},
            ],
        },
    },
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    data_file = tmp_path / "planning.json"
    data_file.write_text(json.dumps(SAMPLE_PLANNING), encoding="utf-8")
    monkeypatch.setattr(api, "DATA_PATH", str(data_file))
    return TestClient(api.app)


def test_health_retourne_200(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_planning_retourne_les_donnees(client):
    r = client.get("/planning")
    assert r.status_code == 200
    data = r.json()
    assert "weeks" in data
    assert "27" in data["weeks"]


def test_planning_semaine_specifique(client):
    r = client.get("/planning/week/27")
    assert r.status_code == 200
    data = r.json()
    assert data["semaine"] == 27
    assert len(data["courses"]) == 2


def test_planning_semaine_inexistante_retourne_404(client):
    r = client.get("/planning/week/99")
    assert r.status_code == 404
    assert "error" in r.json()


def test_planning_sans_fichier_retourne_503(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DATA_PATH", str(tmp_path / "inexistant.json"))
    c = TestClient(api.app)
    r = c.get("/planning")
    assert r.status_code == 503


def test_metrics_retourne_format_prometheus(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"planning_requests_total" in r.content
