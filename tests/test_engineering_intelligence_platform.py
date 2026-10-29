import pytest
from fastapi.testclient import TestClient
from src.main_api import app

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_provenance_summary(client):
    res = client.get("/api/provenance/summary")
    assert res.status_code == 200
    data = res.json()
    assert "providers" in data
    assert "FASTF1" in data["providers"]
    assert "OPENF1" in data["providers"]
    assert "JOLPICA" in data["providers"]
    assert "FIA_DOCUMENTS" in data["providers"]
    assert "confidential_boundaries" in data
    assert len(data["confidential_boundaries"]) >= 5
    assert "classification_definitions" in data
    assert "MEASURED" in data["classification_definitions"]
    assert "UNAVAILABLE" in data["classification_definitions"]

def test_race_operations_endpoints(client):
    # Timing Tower
    res = client.get("/api/race-operations/timing-tower?session_id=S-2024-SPAIN")
    assert res.status_code == 200
    tower = res.json().get("timing_tower", [])
    assert len(tower) >= 15
    assert tower[0]["position"] == 1
    assert "driver_code" in tower[0]
    assert "current_compound" in tower[0]

    # Pit Stops
    res_stops = client.get("/api/race-operations/pit-stops?session_id=S-2024-SPAIN")
    assert res_stops.status_code == 200
    stops = res_stops.json().get("pit_stops", [])
    assert isinstance(stops, list)

    # Race Control
    res_rc = client.get("/api/race-operations/race-control?session_id=S-2024-SPAIN")
    assert res_rc.status_code == 200
    rc_msgs = res_rc.json().get("race_control", [])
    assert len(rc_msgs) > 0

    # Team Radio
    res_radio = client.get("/api/race-operations/team-radio?session_id=S-2024-SPAIN&driver_code=VER")
    assert res_radio.status_code == 200
    radio = res_radio.json().get("team_radio", [])
    assert len(radio) > 0
    assert "transcript" in radio[0]
    assert "strategic_context" in radio[0]

    # Regulations
    res_regs = client.get("/api/race-operations/regulations")
    assert res_regs.status_code == 200
    regs = res_regs.json().get("regulations", [])
    assert len(regs) >= 4
    assert any("Article 28.2" in r["article_reference"] for r in regs)

def test_driver_performance_endpoints(client):
    # Corners
    res_corners = client.get("/api/driver-performance/corners?session_id=S-2024-SPAIN&primary_driver=VER&ref_driver=HAM")
    assert res_corners.status_code == 200
    assert res_corners.json().get("success") is True
    corners = res_corners.json().get("corners", [])
    assert len(corners) > 0
    assert "braking_distance_m" in corners[0]
    assert "apex_speed_kmh" in corners[0]
    assert "peak_deceleration_g" in corners[0]

    # Micro sectors
    res_micro = client.get("/api/driver-performance/micro-sectors?session_id=S-2024-SPAIN&primary_driver=VER&ref_driver=HAM&sectors_count=25")
    assert res_micro.status_code == 200
    assert res_micro.json().get("success") is True
    sectors = res_micro.json().get("micro_sectors", [])
    assert len(sectors) == 25
    assert sectors[0]["dominant_driver"] in ["VER", "HAM"]

    # Driver consistency
    res_cons = client.get("/api/driver-performance/consistency?session_id=S-2024-SPAIN&primary_driver=VER")
    assert res_cons.status_code == 200
    cons = res_cons.json().get("consistency")
    assert cons["driver_id"] == "VER"
    assert cons["consistency_rating_pct"] >= 50.0

    # Ideal lap
    res_ideal = client.get("/api/driver-performance/ideal-lap?session_id=S-2024-SPAIN&primary_driver=VER")
    assert res_ideal.status_code == 200
    ideal = res_ideal.json().get("ideal_lap")
    assert ideal["ideal_lap_s"] <= ideal["actual_best_lap_s"]
    assert "limitations_disclaimer" in ideal

def test_historical_intelligence_endpoints(client):
    # Eras
    res_eras = client.get("/api/historical/eras")
    assert res_eras.status_code == 200
    eras = res_eras.json().get("eras", [])
    assert len(eras) >= 4
    assert any("Ground Effect" in e["era_name"] for e in eras)

    # Teammate H2H
    res_h2h = client.get("/api/historical/teammate-h2h?season=2024")
    assert res_h2h.status_code == 200
    h2h = res_h2h.json().get("head_to_head", [])
    assert len(h2h) >= 4
    assert any(h["team_name"] == "Red Bull Racing" for h in h2h)

    # Championship What If
    res_whatif = client.get("/api/historical/championship-what-if?session_id=S-2024-SPAIN")
    assert res_whatif.status_code == 200
    whatif = res_whatif.json().get("what_if", [])
    assert len(whatif) > 0

def test_model_validation_benchmarks(client):
    res = client.get("/api/model-validation/benchmarks")
    assert res.status_code == 200
    data = res.json()
    assert "benchmarks" in data
    assert len(data["benchmarks"]) >= 4
    for b in data["benchmarks"]:
        assert b["model_mae"] < b["baseline_mae"]
        assert b["is_statistically_superior"] is True
        assert b["data_leakage_guarded"] is True
    assert "calibration_curve" in data
    assert len(data["calibration_curve"]) >= 5
