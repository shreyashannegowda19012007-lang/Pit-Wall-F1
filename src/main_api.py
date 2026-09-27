import os
import sys
import math
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.telemetry_api import api_service
from src import data_ingestion
from src.telemetry_schema import DataStatus

def sanitize_for_json(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (np.integer, np.floating)):
        val = obj.item()
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
        return val
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (datetime, timedelta)):
        return str(obj)
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, np.ndarray, pd.Series)):
        return [sanitize_for_json(v) for v in obj]
    return obj

app = FastAPI(title="Pitwall F1 API", description="FastAPI wrapper for Pitwall F1 Backend")

# Configure CORS
origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return api_service.get_health_status()

@app.get("/api/seasons")
def get_seasons():
    try:
        return api_service.get_available_seasons()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seasons/{season}/rounds")
def get_rounds(season: int):
    try:
        return api_service.get_season_rounds(season)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PrepareSessionRequest(BaseModel):
    season: int
    round_number: int
    session_type: str = "R"

@app.post("/api/sessions/prepare")
def prepare_session(req: PrepareSessionRequest):
    try:
        # Instead of calling api_service.prepare_session which might be mocked/probabilistic,
        # let's use the actual data_ingestion like Streamlit does.
        # Actually, let's look at how Streamlit does it:
        # data_bundle = data_ingestion.fetch_session_data(selected_year, selected_gp, selected_session)
        # We need the event_name, not round_number. Wait, we can get event_name from rounds.

        rounds = api_service.get_season_rounds(req.season)
        gp_name = None
        for r in rounds:
            if r.get("round_number") == req.round_number:
                gp_name = r.get("event_name")
                break

        if not gp_name:
            raise HTTPException(status_code=404, detail="Round not found for season")

        data_bundle = data_ingestion.fetch_session_data(req.season, gp_name, req.session_type)
        if not data_bundle.get("success"):
            raise HTTPException(status_code=500, detail=data_bundle.get("error", "Unknown error"))

        # Do not return full dataframes here, just success.
        # Return summary info.

        results = data_bundle.get("results")
        drivers = results['Abbreviation'].tolist() if (results is not None and 'Abbreviation' in results.columns) else []

        return sanitize_for_json({
            "success": True,
            "drivers": drivers,
            "info": data_bundle.get("info", {}),
            "weather": data_bundle.get("weather", {})
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/telemetry/profile/{driver_id}")
def get_driver_profile(driver_id: str):
    try:
        return api_service.get_driver_performance_profile(driver_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategy/summary")
def get_strategy_summary(session_id: str = "S-2024-SPAIN", lap: int = 22, driver_id: str = "VER"):
    try:
        return api_service.get_canonical_strategy_state(session_id, lap, driver_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timing/summary")
def get_timing_summary(session_id: str = "S-2024-SPAIN"):
    try:
        from src.data_providers import get_provider
        parts = session_id.split('-')
        year = int(parts[1]) if len(parts) > 1 else 2024
        event = parts[2] if len(parts) > 2 else "SPAIN"

        provider = get_provider()
        data = provider.fetch_session_data(year, event, 'R')

        if not data.get("success"):
            raise HTTPException(status_code=500, detail=data.get("error", "Failed to load session data"))

        # Safely convert FastF1 results to a driver list
        results_df = data.get("results")
        drivers = results_df["Abbreviation"].tolist() if results_df is not None and "Abbreviation" in results_df else []

        return {
            "success": True,
            "manifest": {
                "session_id": session_id,
                "status": "READY",
                "weather": {}, # Omit for now or serialize properly
                "drivers": drivers
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/telemetry/compare")
def get_telemetry_compare(session_id: str = "S-2024-SPAIN", target_driver: str = "VER", ref_driver: str = "HAM"):
    try:
        from src.data_providers import get_provider
        from src.telemetry_analysis_service import TelemetryAnalysisService
        import math

        parts = session_id.split('-')
        year = int(parts[1]) if len(parts) > 1 else 2024
        event = parts[2] if len(parts) > 2 else "SPAIN"

        provider = get_provider()
        data = provider.fetch_session_data(year, event, 'R')

        if not data.get("success"):
            status_code = 503 if data.get("status") == DataStatus.UNAVAILABLE else 500
            raise HTTPException(status_code=status_code, detail=data.get("error", "Failed to load session data"))

        session = data.get("raw_session")
        res = TelemetryAnalysisService.compare_laps(session, target_driver, ref_driver)

        if isinstance(res, dict) and not res.get("success", True):
            raise HTTPException(status_code=400, detail=res.get("error", "Failed to analyze telemetry"))

        return sanitize_for_json(res)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# We can add more endpoints as needed for Phase 1.
@app.get("/api/tyres/degradation")
def get_tyre_degradation(session_id: str = "S-2024-SPAIN", primary_driver: str = "VER", ref_driver: str = "HAM"):
    try:
        from src.data_providers import get_provider
        from src.tyre_analytics import TyreAnalyticsEngine
        import math

        parts = session_id.split('-')
        year = int(parts[1]) if len(parts) > 1 else 2024
        event = parts[2] if len(parts) > 2 else "SPAIN"

        provider = get_provider()
        data = provider.fetch_session_data(year, event, 'R')

        if not data.get("success"):
            status_code = 503 if data.get("status") == DataStatus.UNAVAILABLE else 500
            raise HTTPException(status_code=status_code, detail=data.get("error", "Failed to load session data"))

        session = data.get("raw_session")

        # Analyze for both drivers
        primary_res = TyreAnalyticsEngine.analyze_stint_degradation(session, primary_driver)
        ref_res = TyreAnalyticsEngine.analyze_stint_degradation(session, ref_driver)

        if isinstance(primary_res, dict) and not primary_res.get("success", True):
            raise HTTPException(status_code=400, detail=primary_res.get("error", "Failed to analyze primary driver tyre degradation"))
        if isinstance(ref_res, dict) and not ref_res.get("success", True):
            raise HTTPException(status_code=400, detail=ref_res.get("error", "Failed to analyze reference driver tyre degradation"))

        return sanitize_for_json({
            "success": True,
            "primary_driver": primary_res,
            "reference_driver": ref_res
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategy/simulation")
def get_strategy_simulation(session_id: str = "S-2024-SPAIN", primary_driver: str = "VER", ref_driver: str = "HAM"):
    try:
        from src.data_providers import get_provider
        from src.probabilistic_service import ProbabilisticService
        import pandas as pd

        parts = session_id.split('-')
        year = int(parts[1]) if len(parts) > 1 else 2024
        event = parts[2] if len(parts) > 2 else "SPAIN"

        provider = get_provider()
        data = provider.fetch_session_data(year, event, 'R')

        if not data.get("success"):
            status_code = 503 if data.get("status") == DataStatus.UNAVAILABLE else 500
            raise HTTPException(status_code=status_code, detail=data.get("error", "Failed to load session data"))

        session = data.get("raw_session")
        laps = session.laps

        # Find the real gap on track dynamically instead of synthetic hardcode
        primary_laps = laps.pick_driver(primary_driver)
        ref_laps = laps.pick_driver(ref_driver)

        if primary_laps.empty or ref_laps.empty:
            raise HTTPException(status_code=400, detail="Missing driver laps")

        # Get last completed lap by both drivers to calculate track gap
        common_lap = min(primary_laps['LapNumber'].max(), ref_laps['LapNumber'].max())
        p_lap = primary_laps[primary_laps['LapNumber'] == common_lap]
        r_lap = ref_laps[ref_laps['LapNumber'] == common_lap]

        if p_lap.empty or r_lap.empty:
            raise HTTPException(status_code=400, detail="Missing driver lap overlap for gap calculation.")
        else:
            gap_td = p_lap['Time'].iloc[0] - r_lap['Time'].iloc[0]
            gap_s = abs(gap_td.total_seconds())

            # Get median pace
            base_pace = primary_laps.pick_quicklaps()['LapTime'].dt.total_seconds().median()
            if pd.isna(base_pace):
                raise HTTPException(status_code=400, detail="Unable to calculate primary median base pace.")

            rival_base_pace = ref_laps.pick_quicklaps()['LapTime'].dt.total_seconds().median()
            if pd.isna(rival_base_pace):
                raise HTTPException(status_code=400, detail="Unable to calculate rival median base pace.")

        res = ProbabilisticService.analyze_undercut_overcut(primary_driver, ref_driver, gap_s, base_pace, rival_base_pace)

        if isinstance(res, dict) and not res.get("success", True):
            raise HTTPException(status_code=400, detail=res.get("error", "Failed to run probabilistic strategy simulation"))

        # Format the response to match what the frontend expects
        formatted_res = {
            "success": True,
            "undercut_success_probability": res.get("undercut_success_probability_pct", 0) / 100,
            "expected_undercut_time_gain_s": res.get("undercut_expected_gain_s", 0),
            "overcut_success_probability": res.get("overcut_success_probability_pct", 0) / 100,
            "expected_overcut_time_gain_s": res.get("overcut_expected_gain_s", 0),
            "synthetic_scenario": {
                "primary_driver": primary_driver,
                "reference_driver": ref_driver,
                "current_gap_s": round(gap_s, 3),
                "base_pace_s": round(base_pace, 3)
            },
            "recommended_tactic": res.get("recommended_tactic", "unknown")
        }

        return formatted_res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/replay/track")
def get_replay_track(session_id: str = "S-2024-SPAIN", frequency_hz: int = 1):
    try:
        from src.data_providers import get_provider
        from src.replay_service import ReplayService
        import math

        parts = session_id.split('-')
        year = int(parts[1]) if len(parts) > 1 else 2024
        event = parts[2] if len(parts) > 2 else "SPAIN"

        provider = get_provider()
        data = provider.fetch_session_data(year, event, 'R')

        if not data.get("success"):
            status_code = 503 if data.get("status") == DataStatus.UNAVAILABLE else 500
            raise HTTPException(status_code=status_code, detail=data.get("error", "Failed to load session data"))

        session = data.get("raw_session")
        res = ReplayService.extract_track_map(session, frequency_hz)

        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/predict")
def predict_degradation(
    session_id: str = "S-2024-SPAIN",
    compound: str = "MEDIUM",
    fuel_kg: float = 100.0,
    track_temp: float = 35.0
):
    try:
        from src.ml_service import MLService
        res = MLService.predict_degradation(session_id, compound, fuel_kg, track_temp)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jarvis/insights")
def get_jarvis_insights(
    session_id: str = "S-2024-SPAIN",
    primary_driver: str = "VER",
    ref_driver: str = "HAM"
):
    try:
        from src.jarvis_service import JarvisService
        res = JarvisService.generate_insights(session_id, primary_driver, ref_driver)
        if isinstance(res, dict) and not res.get("success", True):
            raise HTTPException(status_code=400, detail=res.get("error", "JARVIS failed to generate insights"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/circuits")
def get_circuits(year: int = 2024):
    try:
        from src.standings_service import StandingsService
        res = StandingsService.get_circuits(year)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/drivers")
def get_drivers(session_id: str = "S-2024-SPAIN"):
    try:
        from src.standings_service import StandingsService
        res = StandingsService.get_drivers(session_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
