import sys
import os
import inspect

sys.path.insert(0, os.path.abspath('src'))
from track_geometry import ensure_track_geometry

def test_ensure_track_geometry_signature():
    sig = inspect.signature(ensure_track_geometry)
    params = list(sig.parameters.keys())
    assert len(params) >= 3, "ensure_track_geometry should accept at least 3 parameters"

def test_ensure_track_geometry_execution():
    result = ensure_track_geometry({}, "Bahrain", 2024)
    assert isinstance(result, dict), "ensure_track_geometry should return a dictionary"
