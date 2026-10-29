"""
Automated Route & Information Architecture Regression Test Suite
Validates that every primary destination, sub-tool, and legacy route remains valid and accessible.
"""
import pytest
import urllib.request
import json
import os

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

# All 14 original and newly structured routes
ROUTES_INVENTORY = [
    # Primary 1: Home
    "/app",
    "/app/home",
    
    # Primary 2: Race Weekend
    "/app/live",
    "/app/command-center",
    "/app/replay",
    "/app/race-weekend",
    "/app/race-weekend/live",
    "/app/race-weekend/command-center",
    "/app/race-weekend/replay",

    # Primary 3: Performance
    "/app/overview",
    "/app/telemetry",
    "/app/comparison",
    "/app/ml-lab",
    "/app/performance",
    "/app/performance/overview",
    "/app/performance/telemetry",
    "/app/performance/comparison",
    "/app/performance/ml-lab",

    # Primary 4: Strategy
    "/app/strategy",
    "/app/monte-carlo",
    "/app/tyres",
    "/app/strategy-hub",
    "/app/strategy/optimizer",
    "/app/strategy/monte-carlo",
    "/app/strategy/tyres",

    # Primary 5: AI Engineer
    "/app/jarvis",
    "/app/ai-engineer",

    # Primary 6: Data & History
    "/app/circuits",
    "/app/drivers",
    "/app/validation",
    "/app/provenance",
    "/app/data-history",
    "/app/data-history/circuits",
    "/app/data-history/drivers",
    "/app/data-history/validation",
    "/app/data-history/provenance"
]

def test_backend_health():
    """Verify backend health and provider availability."""
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/health")
        with urllib.request.urlopen(req, timeout=1) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert data.get("status", "").lower() == "healthy"
    except Exception:
        from fastapi.testclient import TestClient
        from src.main_api import app
        client = TestClient(app)
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json().get("status", "").lower() == "healthy"

def test_live_status():
    """Verify live status endpoint delivers legitimate provider data."""
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/live/status?mode=LIVE")
        with urllib.request.urlopen(req, timeout=1) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
            assert "Official F1 Live Timing" in data.get("provider", "") or "Historical" in data.get("provider", "")
    except Exception:
        from fastapi.testclient import TestClient
        from src.main_api import app
        client = TestClient(app)
        resp = client.get("/api/live/status?mode=LIVE")
        assert resp.status_code == 200
        data = resp.json()
        assert "Official F1 Live Timing" in data.get("provider", "") or "Historical" in data.get("provider", "")

def _is_frontend_server_running():
    try:
        req = urllib.request.Request(FRONTEND_URL)
        with urllib.request.urlopen(req, timeout=0.2) as resp:
            return resp.status == 200
    except Exception:
        return False

_FRONTEND_RUNNING = _is_frontend_server_running()

@pytest.mark.parametrize("route_path", ROUTES_INVENTORY)
def test_frontend_routes_resolve(route_path):
    """Verify every route in the IA inventory resolves (live server or declared in App.tsx)."""
    if _FRONTEND_RUNNING:
        req = urllib.request.Request(f"{FRONTEND_URL}{route_path}")
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            assert resp.status == 200
            content = resp.read().decode()
            assert "<div id=\"root\"></div>" in content
            return

    app_tsx_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "App.tsx")
    assert os.path.exists(app_tsx_path), f"App.tsx not found at {app_tsx_path}"
    with open(app_tsx_path, "r", encoding="utf-8") as f:
        app_content = f.read()

    sub_path = route_path.replace("/app", "").lstrip("/")
    if not sub_path:
        assert '<Route path="/app"' in app_content
    else:
        assert f'path="{sub_path}"' in app_content, f"Route {sub_path} missing in App.tsx"
