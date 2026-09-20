#!/usr/bin/env python3
import sys
import inspect

sys.path.insert(0, 'src')

from track_geometry import ensure_track_geometry

sig = inspect.signature(ensure_track_geometry)
print(f"Function signature: {sig}")
print(f"Parameters: {list(sig.parameters.keys())}")
print(f"Number of parameters: {len(sig.parameters)}")

# Try calling it
try:
    result = ensure_track_geometry({}, "Bahrain", 2024)
    print(f"Function call succeeded")
except TypeError as e:
    print(f"ERROR: {e}")
