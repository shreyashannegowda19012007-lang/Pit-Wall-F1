"""
Fast bootstrap script to build track geometry cache for key F1 circuits.
Prioritizes major tracks and falls back gracefully on errors.
"""

import sys
import os

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from track_geometry import TrackGeometryCache
import json

# Priority circuits - start with these (most commonly used)
PRIORITY_CIRCUITS = [
    ("Spain", 2024),
    ("Monaco", 2024),
    ("Silverstone", 2024),
    ("Monza", 2024),
    ("Austria", 2024),
    ("Singapore", 2024),
    ("Austin", 2024),
    ("Brazil", 2024),
    ("Japan", 2024),
    ("Bahrain", 2024),
]

def bootstrap_tracks():
    """Extract track geometry for priority circuits"""
    results = {}
    
    print("=" * 60)
    print("BOOTSTRAPPING TRACK GEOMETRY CACHE")
    print("=" * 60)
    print(f"Target: {len(PRIORITY_CIRCUITS)} priority circuits\n")
    
    for idx, (location, year) in enumerate(PRIORITY_CIRCUITS, 1):
        print(f"[{idx}/{len(PRIORITY_CIRCUITS)}] Extracting {location} ({year})...", end=" ", flush=True)
        
        try:
            data = TrackGeometryCache.extract_track_from_session(year, location, "R")
            
            if data and data.get("track_x"):
                cache_file = os.path.join(
                    "track_cache",
                    f"{location.lower().replace(' ', '_')}.json"
                )
                os.makedirs("track_cache", exist_ok=True)
                with open(cache_file, 'w', encoding="utf-8") as f:
                    json.dump(data, f)
                
                print(f"âœ“ {data['data_points']} points")
                results[location] = {
                    "status": "success",
                    "data_points": data["data_points"],
                    "year": year,
                }
            else:
                print("âœ— No telemetry data")
                results[location] = {"status": "no_data"}
        
        except Exception as e:
            error_msg = str(e)[:40]
            print(f"âœ— Error: {error_msg}")
            results[location] = {"status": "error", "error": error_msg}
    
    # Summary
    print("\n" + "=" * 60)
    print("BOOTSTRAP COMPLETE")
    print("=" * 60)
    
    successful = sum(1 for r in results.values() if r["status"] == "success")
    print(f"Successfully cached: {successful}/{len(PRIORITY_CIRCUITS)} circuits\n")
    
    for location, result in results.items():
        symbol = "[PASS]" if result["status"] == "success" else "[FAIL]"
        status = result["status"]
        if status == "success":
            print(f"{symbol} {location:20s} - {result['data_points']:3d} points")
        else:
            print(f"{symbol} {location:20s} - {status}")
    
    return results

if __name__ == "__main__":
    bootstrap_tracks()
