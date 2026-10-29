import pytest
from fastapi.testclient import TestClient
from src.main_api import app

client = TestClient(app)

def test_command_center_valid_session():
    response = client.get("/api/command-center?session_id=S-2024-SPAIN&primary_driver=VER&ref_driver=HAM")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session" in data
    assert "primary_driver" in data
    assert "reference_driver" in data
    assert "pace" in data
    assert "strategy" in data
    assert "jarvis" in data
    assert data["primary_driver"]["id"] == "VER"
    assert data["reference_driver"]["id"] == "HAM"

def test_command_center_missing_session():
    response = client.get("/api/command-center?session_id=S-1990-INVALID&primary_driver=VER&ref_driver=HAM")
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] is not None

def test_command_center_missing_driver():
    response = client.get("/api/command-center?session_id=S-2024-SPAIN&primary_driver=XYZ&ref_driver=HAM")
    assert response.status_code == 400
    data = response.json()
    assert "No laps found" in data["detail"]

def test_command_center_driver_switching():
    # Test primary NOR, ref LEC
    response = client.get("/api/command-center?session_id=S-2024-SPAIN&primary_driver=NOR&ref_driver=LEC")
    assert response.status_code == 200
    data = response.json()
    assert data["primary_driver"]["id"] == "NOR"
    assert data["reference_driver"]["id"] == "LEC"
    assert data["success"] is True
