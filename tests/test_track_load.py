import sys
sys.path.insert(0, 'src')
from track_geometry import load_track_geometry

print('Testing track load...')
data = load_track_geometry('Spain', 2024)
print(f"Result: {len(data.get('track_x', []))} points")
print(f"Data keys: {list(data.keys())}")
