import pytest
import pandas as pd
import json
import subprocess
import os
from src.realtime_race_state import DriverRaceState, ReplayAdapter, UnifiedRaceState
import src.production_ml_engine as ml_engine

def test_ml_import():
    # Defect 1: Verify correct import without sys.path hacks
    assert ml_engine is not None
    assert hasattr(ml_engine, "ProductionMLEngine")

def test_driver_race_state_contract():
    # Defect 2: Verify DriverRaceState can be constructed with proper fields
    state = DriverRaceState(
        driver_id="VER",
        driver_name="Max Verstappen",
        number=1,
        team="Red Bull",
        position=1,
        grid_position=1,
        lap_number=42,
        distance_m=0.0,
        sector=1,
        speed_kmh=295.5,
        gear=8,
        throttle_pct=100.0,
        brake_pct=0.0,
        drs_status=0,
        tyre_compound="HARD",
        tyre_age_laps=15,
        stint_number=2,
        pit_status="ON_TRACK",
        gap_to_leader_s=0.0,
        interval_to_ahead_s=0.0,
        last_lap_s=81.2,
        best_lap_s=79.5,
        x=0.0, y=0.0, z=0.0, heading_deg=0.0
    )
    assert state.driver_id == "VER"
    assert state.tyre_compound == "HARD"

def test_replay_adapter_graceful_empty_state():
    # Defect 3: Graceful empty state when data is genuinely missing
    laps_df = pd.DataFrame()

    # Should return empty state, not throw
    adapter = ReplayAdapter(laps_df)
    state = adapter.fetch_current_race_state(session_id="MONACO", timestamp_s=0.0)
    assert isinstance(state, UnifiedRaceState)
    assert len(state.drivers) == 0

def test_replay_adapter_unexpected_exception():
    # Defect 3: Unexpected exceptions (programming errors) should raise, not be swallowed
    # Passing a dataframe without expected columns will trigger an error in pandas operations inside ReplayAdapter
    with pytest.raises(Exception):
        laps_df = pd.DataFrame({"BadColumn": [1, 2, 3]})
        adapter = ReplayAdapter(laps_df)
        adapter.fetch_current_race_state(session_id="MONACO", timestamp_s=0.0)

def test_replay_adapter_real_data_conversion(fastf1_2024_monaco):
    # Defect 7 & 8: Real FastF1 Runtime test
    laps, results, weather, session = fastf1_2024_monaco

    adapter = ReplayAdapter(laps_df=laps, results_df=results)
    # Give a timestamp late in the race so data exists
    state = adapter.fetch_current_race_state(session_id="MONACO", timestamp_s=4000.0)
    assert isinstance(state, UnifiedRaceState)

    # Require drivers > 0 and verify at least 5 drivers contain valid state
    assert len(state.drivers) > 0
    valid_drivers = [d for d in state.drivers.values() if d.driver_id and d.position > 0]
    assert len(valid_drivers) >= 5

def test_timing_tower_real_data(fastf1_2024_monaco):
    # Defect 9: Timing Tower Real Data Test
    laps, results, weather, session = fastf1_2024_monaco

    adapter = ReplayAdapter(laps_df=laps, results_df=results)
    state = adapter.fetch_current_race_state(session_id="MONACO", timestamp_s=4000.0)
    assert len(state.drivers) > 0

    from src.pitwall_ui import render_unified_realtime_timing_tower
    from unittest.mock import patch

    try:
        with patch("src.telemetry_api.api_service.get_unified_race_state", return_value=state):
            render_unified_realtime_timing_tower()
        rendered_successfully = True
    except Exception as e:
        rendered_successfully = False
        pytest.fail(f"render_unified_realtime_timing_tower raised an exception: {e}")

    assert rendered_successfully

def test_windows_validation_output():
    # Defect 6: Windows-safe validation output
    # Check that bootstrap_track_cache.py (or any script generating output) uses PASS/FAIL instead of checkmarks
    with open("bootstrap_track_cache.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert "[PASS]" in content
    assert "✓" not in content

@pytest.fixture(scope="module")
def fastf1_2024_monaco():
    import fastf1
    # Use fastf1 to fetch real data
    # We can use the existing data_ingestion module if it works
    from src import data_ingestion
    bundle = data_ingestion.fetch_session_data(2024, "Monaco", "Race")
    assert bundle["success"] is True
    session = bundle["raw_session"]
    laps = bundle["laps"]
    results = bundle["results"]
    weather = session.weather_data if hasattr(session, "weather_data") else pd.DataFrame()
    return laps, results, weather, session
