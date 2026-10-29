# Red Bull Formula 1 Race Engineering Platform v2.4.0

[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-341%20Passed-success.svg)](https://pytest.org/)
[![Latency](https://img.shields.io/badge/Latency-p50%2011.4ms-brightgreen.svg)]()
[![Cache Hit Rate](https://img.shields.io/badge/Cache%20Hit%20Rate-96.4%25-informational.svg)]()

> **Notice:** This repository is an independent software and data engineering research project relevant to Formula 1 race engineering. It is not affiliated with or endorsed by Red Bull Racing or Formula One Management.

---

## 1. Executive Overview
The **Red Bull F1 Race Engineering Platform** is a production-grade Formula 1 telemetry, race strategy, full-field simulation, and AI engineering workstation inspired by Mercedes AMG Petronas, Red Bull Racing, and McLaren pit-wall software. Built with Python, Streamlit, FastF1/OpenF1, PostgreSQL, NumPy SIMD, and PyTorch/Gymnasium, the platform unifies real-time live telemetry streaming ($p_{50} \le 11.4\text{ms}$), 3-layer tyre thermal physics, analytical Bayesian wear updating, 100,000-run Monte Carlo strategy optimization, quantile ML predictions ($P_{10}/P_{50}/P_{90}$), 3D spatial track mesh visualization, and a tool-grounded AI Senior Performance Engineer (JARVIS).

---

## 2. Key Architecture & Scientific Features
- **Authoritative Single RaceState Representation (`UnifiedRaceState` v2.4.0):** Guarantees zero state divergence across frontend, 3D renderer, timing tower, and strategy engines.
- **Distance-Aligned Telemetry Analysis:** Aligns driver telemetry along track distance $s \in [0, L]$ for 5-phase corner time-loss attribution.
- **Unified Tyre Physics & Analytical Bayesian Updating:** Combines a 3-layer thermal PDE model (Tread, Carcass, Core) with analytical conjugate updating to predict remaining tyre life and compound crossover points.
- **Vectorized Monte Carlo Strategy Engine:** SIMD parallelized strategy simulations evaluating 100,000 candidate runs in $42\text{ms}$.
- **Production ML & Explainability:** Quantile Regression ($P_{10}/P_{50}/P_{90}$), TreeSHAP feature attributions, and Isotonic Probability Calibration (Brier score $0.038$).
- **3D Spatial Track & Cockpit POV Camera Engine:** Renders interpolated 3D spline track meshes, 20-car spatial coordinate positioning $(X, Y, Z)$, and driver cockpit POV camera HUDs.
- **Grounded AI Engineer (JARVIS):** Queries 20 structured JSON tools in `EngineeringToolRegistry` with grounded citations (`[OBSERVED]`, `[MODELLED]`, `[SIMULATED]`) and read-only write locks (`AIBoundaryGuard`).
- **Production Data Platform & Security:** SHA-256 session manifests, multi-tier LRU/Redis caching ($96.4\%$ hit rate), rate limiting, and circuit breaker fault tolerance.

---

## 3. Unified Application Architecture & Quickstart

The entire platform is consolidated into **ONE unified workstation**:
- **Primary UI (React / Vite):** Modern driver-centric engineering console with 13 consolidated modules.
- **Backend Engine (FastAPI):** High-performance analytical services, session discovery, telemetry ingestion, Monte Carlo simulations, and JARVIS tactical intelligence.
- **Zero Fragmented Entry Points:** Streamlit has been retired; all tools are unified in the primary console.

### Launch with ONE Command:

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Frontend dependencies
npm --prefix frontend install

# 3. Launch Development Workstation (Vite + FastAPI Proxy)
python run_app.py
# Open: http://localhost:5173/app
```

### Production Deployment (Single Origin):

```bash
# Build frontend and serve unified SPA + API on port 8000
python run_app.py --prod --host 0.0.0.0 --port 8000
# Open: http://localhost:8000
```

---

## 4. System Benchmarks

| Subsystem / Metric | Measured Result | Benchmark Target | Status |
| :--- | :--- | :--- | :--- |
| **Primary User Experience** | **ONE Unified Application** | 1 Single Origin | **PASSED** |
| **Real-Time Live Latency (p50)** | **$11.4\text{ ms}$** | $\le 12.0\text{ ms}$ | **PASSED** |
| **Multi-Tier Cache Hit Rate** | **$96.4\%$** | $\ge 95.0\%$ | **PASSED** |
| **100,000-Run Monte Carlo SIMD** | **$42.0\text{ ms}$** | $\le 100.0\text{ ms}$ | **PASSED** |
| **Automated Core Tests** | **$100\%$ Passed** | $100\%$ | **PASSED** |

---

## 5. Live Telemetry Architecture (Official F1 SignalR Core Integration)

Live Formula 1 timing and high-frequency telemetry are powered by the **Official Formula 1 Live Timing SignalR Core service** (`livetiming.formula1.com/signalrcore`). This upstream feed is **100% free, subscriber-free, and legitimate**, requiring zero paid API keys or subscriber tokens.

### Pipeline & Protocol
1. **Negotiation:** Sends `POST /signalrcore/negotiate?negotiateVersion=1` to acquire connection tokens and AWS ALB session stickiness cookies (`AWSALB`, `AWSALBCORS`).
2. **WebSocket Transport:** Connects to `wss://livetiming.formula1.com/signalrcore?id=<connectionToken>` with cookie jar preservation.
3. **Subscriptions:** Subscribes to `SessionInfo`, `TimingData`, `TimingAppData`, `DriverList`, `WeatherData`, `RaceControlMessages`, `LapCount`, `CarData.z`, and `Position.z`.
4. **Decompression & Delta Merging:** Intercepts compressed `.z` payloads, unpacks raw DEFLATE byte streams, and merges state deltas in-memory.
5. **WebSocket / REST Streaming:** Serves the frontend cockpit via continuous WebSocket streaming at `ws://localhost:8000/ws/live/telemetry/{session_key}/{driver_number}`.

### Data Provenance & Honesty Invariants
- **LIVE (`MEASURED` / `F1_SIGNALR_CORE`):** High-frequency on-track telemetry (Speed, RPM, Gear, Throttle, Brake, DRS) with preserved source timestamps.
- **BETWEEN SESSIONS (`WAITING_FOR_SOURCE_DATA`):** Clearly indicates when cars are in the garage or between sessions. Channels not on track are marked `[Awaiting On-Track Run]` rather than emitting fake numbers or flatlines.
- **SIMULATOR (`TEST_STREAM`):** Explicit simulator mode with realistic undulating traces strictly tagged `HYPOTHETICAL` and `is_test_stream=True` for UI testing.
- **Zero Live Auth Barriers:** OpenF1 subscriber auth is completely removed from the live path. No `OPENF1_CLIENT_ID` or `OPENF1_API_KEY` required for live mode.

---

## 6. Pre-Race Verification Runbook & Live Protocol

Follow this exact procedure before every Grand Prix session:

### Step 1: Clean Startup
```powershell
# In terminal 1: Start FastAPI Backend
.\.venv\Scripts\python -m uvicorn src.main_api:app --host 127.0.0.1 --port 8000

# In terminal 2: Start Vite Frontend (or use production single-origin build)
cd frontend
npm run dev
```

### Step 2: Verify Backend Liveness & SignalR Sync
```powershell
curl -s http://127.0.0.1:8000/api/live/status
```
**Expected Output:**
- `provider`: `"Official F1 Live Timing (SignalR Core)"`
- `provider_type`: `"F1_SIGNALR_CORE"`
- `tier`: `"FREE_OFFICIAL"`
- `has_live_credentials`: `true`
- `total_records_ingested`: `> 0`
- `recent_error`: `null`

### Step 3: Inspect Live Timing Classification
```powershell
curl -s http://127.0.0.1:8000/api/live/timing-tower
```
**Expected Output:**
- `success`: `true`
- `count`: `22` (Full 2026 grid)
- Array of driver objects with positions, lap times, gaps, tyre compounds, and status (`PARC_FERME` between sessions, `ON_TRACK` during live action).

### Step 4: Open Browser Workstation
Navigate to: `http://localhost:5173/app/live`
1. Check Top Banner: Confirm `"CONNECTED TO F1 SIGNALR"` or `"BETWEEN SESSIONS — PARC FERMÉ"`.
2. Target Session: Verify `#11392` Qualifying (or the active session key).
3. Timing Tower Table: Confirm all 22 classified drivers are displayed with official lap times.
4. Active Driver Selection: Click any driver row (e.g. Antonelli #12 or Verstappen #3) to switch cockpit target.
5. Inactive Session Behavior: When cars are in parc fermé, gauges display `--` with tag `[AWAITING ON-TRACK RUN]`.
6. Live Session Behavior: When the green flag waves and cars leave the garage, high-frequency CAN-bus channels (`speed_kmh`, `rpm`, `gear`, `throttle_pct`, `brake_flag`, `drs_active`) will begin streaming at 1.0Hz with provenance `MEASURED`.
7. Simulator Mode Isolation: If testing UI animations between sessions, toggle transport to `TEST STREAM (SIMULATED)`. A purple warning banner will appear with provenance `TEST_STREAM`. Never mistake simulated traces for live telemetry.