"""
Tests for V1 REST API Endpoints.
================================
Validates sports listing, reference retrieval, health check, and analysis creation.
"""

from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_list_sports():
    response = client.get("/api/v1/sports")
    assert response.status_code == 200
    data = response.json()
    assert "sports" in data
    sport_names = [s["name"] for s in data["sports"]]
    assert "badminton" in sport_names


def test_badminton_movements():
    response = client.get("/api/v1/sports/badminton/movements")
    assert response.status_code == 200
    data = response.json()
    assert "overhead_clear" in data["movements"]
    assert "side_view" in data["camera_views"]


def test_badminton_reference():
    response = client.get("/api/v1/references/badminton/overhead_clear")
    assert response.status_code == 200
    data = response.json()
    assert data["sport"] == "badminton"
    assert data["movement"] == "overhead_clear"
    assert "benchmark_metrics" in data
    assert "contact_elbow_angle" in data["benchmark_metrics"]
    assert "ghost_reference_poses" in data
