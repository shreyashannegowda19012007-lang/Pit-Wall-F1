import urllib.request
import json
import sys

endpoints = [
    '/api/health',
    '/api/seasons',
    '/api/seasons/2024/rounds',
    '/api/timing/summary?session_id=S-2024-SPAIN',
    '/api/telemetry/profile/VER?session_id=S-2024-SPAIN',
    '/api/strategy/summary?session_id=S-2024-SPAIN&driver_id=VER',
    '/api/command-center?session_id=S-2024-SPAIN&primary_driver=VER&ref_driver=HAM',
    '/api/jarvis/insights?session_id=S-2024-SPAIN&primary_driver=VER&ref_driver=HAM',
    '/api/telemetry/compare?session_id=S-2024-SPAIN&target_driver=VER&ref_driver=HAM',
    '/api/tyres/degradation?session_id=S-2024-SPAIN&primary_driver=VER&ref_driver=HAM',
    '/api/strategy/simulation?session_id=S-2024-SPAIN&primary_driver=VER&ref_driver=HAM',
    '/api/ml/predict?session_id=S-2024-SPAIN&compound=MEDIUM&fuel_kg=100&track_temp=35',
    '/api/circuits?year=2024',
    '/api/drivers?session_id=S-2024-SPAIN',
    '/api/simulations/monte_carlo?session_id=S-2024-SPAIN&target_driver=VER&num_sims=10',
    '/api/standings/drivers?year=2024',
    '/api/standings/constructors?year=2024',
    '/api/live/status',
    '/api/live/sessions',
    '/api/live/drivers?session_key=11390',
    '/api/live/telemetry/latest?session_key=11390&driver_number=1',
    '/api/live/telemetry/moving?session_key=11390&driver_number=1&limit=5',
    '/api/live/telemetry/test-stream?session_key=11390&driver_number=1&step=0',
    '/api/provenance/summary',
    '/api/driver-performance/corners?session_id=S-2024-SPAIN&primary_driver=VER&ref_driver=HAM',
    '/api/driver-performance/micro-sectors?session_id=S-2024-SPAIN&primary_driver=VER&ref_driver=HAM&sectors_count=10',
    '/api/driver-performance/consistency?session_id=S-2024-SPAIN&primary_driver=VER',
    '/api/driver-performance/ideal-lap?session_id=S-2024-SPAIN&primary_driver=VER',
    '/api/race-operations/timing-tower?session_id=S-2024-SPAIN',
    '/api/race-operations/pit-stops?session_id=S-2024-SPAIN',
    '/api/race-operations/race-control?session_id=S-2024-SPAIN',
    '/api/race-operations/team-radio?session_id=S-2024-SPAIN&driver_code=VER',
    '/api/race-operations/regulations',
    '/api/historical/eras',
    '/api/historical/teammate-h2h?season=2024',
    '/api/historical/championship-what-if?session_id=S-2024-SPAIN',
    '/api/model-validation/benchmarks'
]

print(f"Testing {len(endpoints)} API endpoints on http://127.0.0.1:8000...", flush=True)
passed = 0
failed = 0
for ep in endpoints:
    url = 'http://127.0.0.1:8000' + ep
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PitwallAuditor/1.0'})
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"[PASS] {resp.status} : {ep}", flush=True)
            passed += 1
    except Exception as e:
        print(f"[FAIL] {ep} -> {e}", flush=True)
        failed += 1

print(f"\nFinal Endpoint Audit Results: {passed} PASSED, {failed} FAILED out of {len(endpoints)}", flush=True)
if failed > 0:
    sys.exit(1)
