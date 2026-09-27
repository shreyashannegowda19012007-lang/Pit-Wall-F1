import pytest
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath('src'))

from src.pitwall_ui import render_timing_tower, render_session_header, get_tyre_html
from src.strategy_simulator import render_jarvis_deck, render_strategy_timeline
from src.race_simulator import render_simulator_ui

class DummySession:
    def __init__(self):
        self.event = {'RaceLaps': 50, 'EventName': 'Test GP'}
        self.weather_data = pd.DataFrame([{'TrackTemp': 35.0, 'AirTemp': 25.0, 'Rainfall': False}])

def test_timing_tower_real_data():
    results = pd.DataFrame([{'Driver': 'VER', 'Abbreviation': 'VER', 'Position': 1, 'GridPosition': 1, 'DriverNumber': '1', 'TeamName': 'Red Bull'}])
    laps = pd.DataFrame([{'Driver': 'VER', 'LapNumber': 1, 'LapTime': pd.to_timedelta(90, unit='s'), 'Sector1Time': pd.to_timedelta(30, unit='s'), 'Sector2Time': pd.to_timedelta(30, unit='s'), 'Sector3Time': pd.to_timedelta(30, unit='s'), 'Compound': 'SOFT', 'TyreLife': 5}])
    try:
        render_timing_tower(results, laps)
    except Exception as e:
        pytest.fail(f"render_timing_tower failed: {e}")

def test_session_header_real_data():
    info = {'TrackTemp': 30.0, 'AirTemp': 25.0, 'Rainfall': False}
    weather = pd.DataFrame([{'Humidity': 50, 'WindSpeed': 2.5}])
    try:
        render_session_header(info, weather)
    except Exception as e:
        pytest.fail(f"render_session_header failed: {e}")

def test_get_tyre_html():
    html = get_tyre_html('SOFT', 5)
    assert 'S' in html
    assert '5' in html

def test_render_jarvis_deck():
    laps = pd.DataFrame([{'Driver': 'VER', 'LapNumber': 1, 'Compound': 'SOFT', 'TyreLife': 5}])
    results = pd.DataFrame([{'Driver': 'VER', 'Position': 1}])
    info = {'official_name': 'Test GP'}
    try:
        render_jarvis_deck(DummySession(), 'VER', laps, results, info)
    except Exception as e:
        pytest.fail(f"render_jarvis_deck failed: {e}")

def test_render_strategy_timeline():
    laps = pd.DataFrame([{'Driver': 'VER', 'LapNumber': 1, 'Stint': 1, 'Compound': 'SOFT', 'TyreLife': 5}])
    try:
        render_strategy_timeline(laps)
    except Exception as e:
        pytest.fail(f"render_strategy_timeline failed: {e}")

def test_render_simulator_ui():
    laps = pd.DataFrame([{'Driver': 'VER', 'LapNumber': 1, 'Time': pd.to_timedelta(10, unit='s'), 'LapTime': pd.to_timedelta(90, unit='s'), 'Compound': 'SOFT', 'TyreLife': 5}])
    session = DummySession()
    try:
        render_simulator_ui(session, laps, 'VER', 10, 'Medium', 'Green Flag', 'Medium')
    except Exception as e:
        pytest.fail(f"render_simulator_ui failed: {e}")
