import sys
import os
sys.path.insert(0, os.path.abspath('src'))
from track_geometry import load_track_geometry

def test_load_track_geometry():
    data = load_track_geometry('Spain', 2024)
    assert isinstance(data, dict), "Track geometry should return a dictionary"
    assert 'track_x' in data, "Track geometry must contain track_x coordinates"
    assert 'track_y' in data, "Track geometry must contain track_y coordinates"
    assert len(data.get('track_x', [])) > 0, "Track geometry should have non-empty track_x"
    assert len(data.get('track_y', [])) > 0, "Track geometry should have non-empty track_y"
