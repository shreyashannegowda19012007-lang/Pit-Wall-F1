# Pitwall F1 Architecture & Telemetry Guardrails

## 1. Single Unified Entry Point
- The application is consolidated around the FastAPI backend (`src/main_api.py`) on port 8000 and the React 19 / Vite frontend on port 5173 (development) or served directly as a static SPA by FastAPI (production) via `run_app.py`.
- Never launch or promote competing application entry points (e.g., Streamlit `src/app.py`) for primary workflows.
- `Dockerfile` and `docker-compose.yml` must expose port 8000 and execute `python run_app.py --prod --host 0.0.0.0 --port 8000`.

## 2. Strict Data Provenance & Zero Fabrication
- Every telemetry trace and derived metric must be classified into one of the 5 canonical tiers: `MEASURED`, `DERIVED`, `ESTIMATED`, `HYPOTHETICAL`, or `UNAVAILABLE`.
- Never fabricate speed, RPM, gear, throttle, brake, or lap times when off-track.
- When between sessions or offline, the system must declare `BETWEEN SESSIONS / STANDBY` honestly rather than presenting simulated data as live.

## 3. Telemetry Ingestion Hierarchy
- **Live Ingestion**: Official F1 Live Timing SignalR Core (`livetiming.formula1.com/signalrcore`) is the primary zero-cost live streaming provider (`src/f1_signalr_service.py`).
- **Historical Ingestion**: FastF1 with local Parquet/SQLite caching (`fastf1_cache/`) is the primary historical provider.
- **Historical Replay**: Stream cached FastF1 telemetry through the replay state machine (`src/historical_replay_service.py`) with explicit `HISTORICAL_REPLAY` provenance badges.

## 4. Dependency Synchronization
- Always keep `requirements.txt`, `Dockerfile`, and `docker-compose.yml` synchronized with the actual dependencies imported by `src/main_api.py` (`fastapi`, `uvicorn`, `websockets`, `aiohttp`, `signalrcore`, `pydantic`).
- Purge temporary scratch dump files (*.json, *.txt, *.err) from root to maintain a clean workspace.
