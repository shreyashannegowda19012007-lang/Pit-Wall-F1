import os
import sys
import math
import logging
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import asdict

logger = logging.getLogger("main_api")

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.telemetry_api import api_service
from src import data_ingestion
from src.telemetry_schema import DataStatus
from src.command_center_service import CommandCenterService
from src.session_utils import parse_session_id, pick_driver_laps

def sanitize_for_json(obj):
    if obj is None:
        return None
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    if hasattr(obj, 'item') and callable(obj.item):
        return sanitize_for_json(obj.item())
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (datetime, timedelta)):
        return str(obj)
    if isinstance(obj, pd.DataFrame):
        return [sanitize_for_json(r) for r in obj.to_dict(orient='records')]
    if isinstance(obj, pd.Series):
        return {str(k): sanitize_for_json(v) for k, v in obj.to_dict().items()}
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, np.ndarray)):
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

@app.on_event("startup")
async def startup_live_provider():
    try:
        from src.f1_signalr_service import f1_signalr_provider
        await f1_signalr_provider.start()
        logger.info("F1 SignalR provider started.")
    except Exception as e:
        logger.warning(f"Could not start F1 SignalR provider: {e}")

@app.on_event("shutdown")
async def shutdown_live_provider():
    try:
        from src.f1_signalr_service import f1_signalr_provider
        await f1_signalr_provider.stop()
        logger.info("F1 SignalR provider stopped.")
    except Exception as e:
        logger.warning(f"Error stopping F1 SignalR provider: {e}")
    try:
        from src.historical_replay_service import historical_replay_service
        await historical_replay_service.stop_replay()
        logger.info("Historical replay worker stopped.")
    except Exception as e:
        logger.warning(f"Error stopping historical replay service: {e}")

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
def get_driver_profile(driver_id: str, session_id: str = "S-2024-SPAIN"):
    try:
        return api_service.get_driver_performance_profile(driver_id, session_id)
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
        year, event, session_type = parse_session_id(session_id)

        provider = get_provider()
        data = provider.fetch_session_data(year, event, session_type)

        if not data.get("success"):
            raise HTTPException(status_code=500, detail=data.get("error", "Failed to load session data"))

        # Safely convert FastF1 results to a driver list
        results_df = data.get("results")
        drivers = results_df["Abbreviation"].tolist() if results_df is not None and "Abbreviation" in results_df else []
        weather = data.get("weather", {})

        return {
            "success": True,
            "manifest": {
                "session_id": session_id,
                "status": "READY",
                "weather": sanitize_for_json(weather),
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

        year, event, session_type = parse_session_id(session_id)

        provider = get_provider()
        data = provider.fetch_session_data(year, event, session_type)

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


@app.get("/api/command-center")
def get_command_center(session_id: str = "S-2024-SPAIN", primary_driver: str = "VER", ref_driver: str = "HAM"):
    try:
        res = CommandCenterService.get_command_center_data(session_id, primary_driver, ref_driver)
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("error", "Failed to load command center data"))
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

        year, event, session_type = parse_session_id(session_id)

        provider = get_provider()
        data = provider.fetch_session_data(year, event, session_type)

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

        year, event, session_type = parse_session_id(session_id)

        provider = get_provider()
        data = provider.fetch_session_data(year, event, session_type)

        if not data.get("success"):
            status_code = 503 if data.get("status") == DataStatus.UNAVAILABLE else 500
            raise HTTPException(status_code=status_code, detail=data.get("error", "Failed to load session data"))

        session = data.get("raw_session")
        laps = session.laps

        primary_laps = pick_driver_laps(laps, primary_driver)
        ref_laps = pick_driver_laps(laps, ref_driver)

        if primary_laps.empty or ref_laps.empty:
            raise HTTPException(status_code=400, detail="Missing driver laps")

        common_lap = min(primary_laps['LapNumber'].max(), ref_laps['LapNumber'].max())
        p_lap = primary_laps[primary_laps['LapNumber'] == common_lap]
        r_lap = ref_laps[ref_laps['LapNumber'] == common_lap]

        if p_lap.empty or r_lap.empty:
            raise HTTPException(status_code=400, detail="Missing driver lap overlap for gap calculation.")

        gap_td = (p_lap['Time'].iloc[0] - r_lap['Time'].iloc[0]).total_seconds()
        gap_s = abs(gap_td)
        primary_is_ahead = gap_td < 0

        p_quick = primary_laps.pick_quicklaps()
        r_quick = ref_laps.pick_quicklaps()

        base_pace = p_quick['LapTime'].dt.total_seconds().median() if not p_quick.empty else primary_laps['LapTime'].dt.total_seconds().median()
        if pd.isna(base_pace):
            raise HTTPException(status_code=400, detail="Unable to calculate primary median base pace.")

        rival_base_pace = r_quick['LapTime'].dt.total_seconds().median() if not r_quick.empty else ref_laps['LapTime'].dt.total_seconds().median()
        if pd.isna(rival_base_pace):
            raise HTTPException(status_code=400, detail="Unable to calculate rival median base pace.")

        res = ProbabilisticService.analyze_undercut_overcut(
            primary_driver, ref_driver, gap_s, base_pace, rival_base_pace, primary_is_ahead=primary_is_ahead
        )

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
                "base_pace_s": round(base_pace, 3),
                "primary_is_ahead": primary_is_ahead
            },
            "recommended_tactic": res.get("recommended_tactic", "unknown"),
            "tactic": res.get("tactic", "maintain")
        }

        return formatted_res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/replay/track")
def get_replay_track(session_id: str = "S-2024-SPAIN", frequency_hz: int = 2):
    try:
        from src.data_providers import get_provider
        from src.replay_service import ReplayService

        year, event, session_type = parse_session_id(session_id)

        provider = get_provider()
        data = provider.fetch_session_data(year, event, session_type)

        if not data.get("success"):
            status_code = 503 if data.get("status") == DataStatus.UNAVAILABLE else 500
            raise HTTPException(status_code=status_code, detail=data.get("error", "Failed to load session data"))

        session = data.get("raw_session")
        res = ReplayService.extract_track_map(session, frequency_hz=frequency_hz, session_id=session_id)

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

@app.get("/api/simulations/monte_carlo")
def get_monte_carlo_simulation(
    target_driver: str = "VER",
    circuit_id: str = "SPAIN",
    total_laps: Optional[int] = None,
    num_sims: int = 250,
    session_id: Optional[str] = None,
    objective: str = "BALANCED",
    evaluation_mode: str = "PRE_RACE",
    season: Optional[int] = None,
    deg_multiplier: float = 1.0,
    pit_loss_offset_s: float = 0.0,
    sc_prob_override: Optional[float] = None
):
    try:
        from src.session_utils import parse_session_id
        from src.circuit_database import CircuitDatabase
        from src.global_strategy_engine import GlobalStrategyEngine

        actual_season = season or 2025
        actual_circuit = circuit_id
        prof = CircuitDatabase.get_circuit_profile(actual_circuit)
        actual_laps = total_laps if (total_laps and total_laps > 0) else prof.scheduled_laps

        if session_id:
            try:
                year, event, session_type = parse_session_id(session_id)
                actual_season = year
                if event:
                    clean_ev = str(event).replace("Grand Prix", "").strip()
                    resolved_key = CircuitDatabase.resolve_circuit_key(clean_ev)
                    prof = CircuitDatabase.get_circuit_profile(resolved_key)
                    actual_circuit = prof.circuit_id
                    actual_laps = prof.scheduled_laps
            except Exception:
                pass

        if total_laps and total_laps > 0:
            actual_laps = total_laps

        sim_count = max(20, min(num_sims, 5000))
        strategy_res = GlobalStrategyEngine.run_global_simulation(
            target_driver=target_driver,
            circuit_id=actual_circuit,
            season=actual_season,
            total_laps=actual_laps,
            num_sims=sim_count,
            objective=objective,
            evaluation_mode=evaluation_mode,
            user_deg_multiplier=deg_multiplier,
            user_pit_loss_offset_s=pit_loss_offset_s,
            user_sc_prob_override=sc_prob_override
        )

        field_rankings = strategy_res.get("field_rankings", [])
        field_res = {
            "num_simulations": strategy_res.get("completed_iterations", sim_count),
            "circuit_id": actual_circuit,
            "total_laps": actual_laps,
            "driver_rankings": field_rankings
        }

        return sanitize_for_json({
            "success": True,
            "target_driver": target_driver,
            "season": actual_season,
            "circuit_id": actual_circuit,
            "circuit_name": strategy_res.get("circuit_name", prof.canonical_name),
            "total_laps": actual_laps,
            "completed_iterations": strategy_res.get("completed_iterations", sim_count),
            "objective_used": strategy_res.get("objective_used", objective),
            "evaluation_mode": evaluation_mode,
            "physical_nominations": strategy_res.get("physical_nominations", {}),
            "circuit_profile": strategy_res.get("circuit_profile", {}),
            "strategy_simulation": strategy_res,
            "field_simulation": field_res,
            "invariants_verified": strategy_res.get("invariants_verified", {})
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/standings/drivers")
def get_driver_standings(year: int = 2024, round_number: Optional[int] = None):
    try:
        from src.standings_service import StandingsService
        res = StandingsService.get_driver_standings(year, round_number)
        return sanitize_for_json(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/standings/constructors")
def get_constructor_standings(year: int = 2024, round_number: Optional[int] = None):
    try:
        from src.standings_service import StandingsService
        res = StandingsService.get_constructor_standings(year, round_number)
        return sanitize_for_json(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live/status")
def get_live_status(mode: Optional[str] = None):
    try:
        from src.live_provider_factory import get_live_provider
        provider = get_live_provider(mode=mode)
        return sanitize_for_json(provider.get_live_status())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/telemetry/export")
def export_telemetry_csv(
    session_id: str = "S-2024-SPAIN",
    target_driver: str = "VER",
    ref_driver: str = "HAM"
):
    try:
        from src.report_service import ReportService
        csv_str, filename = ReportService.export_telemetry_csv(session_id, target_driver, ref_driver)
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/comparison/export")
def export_comparison_csv(
    session_id: str = "S-2024-SPAIN",
    target_driver: str = "VER",
    ref_driver: str = "HAM"
):
    try:
        from src.report_service import ReportService
        csv_str, filename = ReportService.export_comparison_csv(session_id, target_driver, ref_driver)
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/strategy/export")
def export_strategy_report(
    session_id: str = "S-2024-SPAIN",
    primary_driver: str = "VER",
    ref_driver: str = "HAM"
):
    try:
        from src.report_service import ReportService
        report = ReportService.export_strategy_brief(session_id, primary_driver, ref_driver)
        return sanitize_for_json(report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# PHASE 1 - 9: ADVANCED ENGINEERING INTELLIGENCE API ROUTES
# =========================================================================

@app.get("/api/provenance/summary")
def get_provenance_summary():
    try:
        from src.data_provenance import DataProvenanceRegistry
        return sanitize_for_json(DataProvenanceRegistry.get_provenance_summary())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/driver-performance/corners")
def get_driver_performance_corners(
    session_id: str = "S-2024-SPAIN",
    primary_driver: str = "VER",
    ref_driver: str = "HAM"
):
    try:
        from src.driver_performance_engine import DriverPerformanceEngine
        from src.data_ingestion import fetch_session_data
        from src.session_utils import parse_session_id
        
        year, event, session_type = parse_session_id(session_id)
        data = fetch_session_data(year, event, session_type)
        laps = data.get("laps")
        if laps is None or laps.empty:
            return {"success": False, "corners": []}
            
        drv_laps = laps[laps['Driver'] == primary_driver]
        ref_laps = laps[laps['Driver'] == ref_driver]
        if drv_laps.empty or ref_laps.empty:
            return {"success": False, "corners": []}
            
        drv_t = drv_laps.pick_fastest().get_telemetry()
        ref_t = ref_laps.pick_fastest().get_telemetry()
        
        drv_dyn = DriverPerformanceEngine.compute_vehicle_dynamics(drv_t)
        ref_dyn = DriverPerformanceEngine.compute_vehicle_dynamics(ref_t)
        
        corners = DriverPerformanceEngine.decompose_corners(drv_dyn, ref_dyn)
        return sanitize_for_json({
            "success": True,
            "session_id": session_id,
            "primary_driver": primary_driver,
            "ref_driver": ref_driver,
            "corners": [asdict(c) for c in corners]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/driver-performance/micro-sectors")
def get_driver_performance_micro_sectors(
    session_id: str = "S-2024-SPAIN",
    primary_driver: str = "VER",
    ref_driver: str = "HAM",
    sectors_count: int = 25
):
    try:
        from src.driver_performance_engine import DriverPerformanceEngine
        from src.data_ingestion import fetch_session_data
        from src.session_utils import parse_session_id
        
        year, event, session_type = parse_session_id(session_id)
        data = fetch_session_data(year, event, session_type)
        laps = data.get("laps")
        if laps is None or laps.empty:
            return {"success": False, "micro_sectors": []}
            
        drv_laps = laps[laps['Driver'] == primary_driver]
        ref_laps = laps[laps['Driver'] == ref_driver]
        if drv_laps.empty or ref_laps.empty:
            return {"success": False, "micro_sectors": []}
            
        drv_t = drv_laps.pick_fastest().get_telemetry()
        ref_t = ref_laps.pick_fastest().get_telemetry()
        
        deltas = DriverPerformanceEngine.compute_micro_sectors(drv_t, ref_t, primary_driver, ref_driver, sectors_count)
        return sanitize_for_json({
            "success": True,
            "session_id": session_id,
            "primary_driver": primary_driver,
            "ref_driver": ref_driver,
            "micro_sectors": [asdict(d) for d in deltas]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/driver-performance/consistency")
def get_driver_performance_consistency(
    session_id: str = "S-2024-SPAIN",
    primary_driver: str = "VER"
):
    try:
        from src.driver_performance_engine import DriverPerformanceEngine
        from src.data_ingestion import fetch_session_data
        from src.session_utils import parse_session_id
        
        year, event, session_type = parse_session_id(session_id)
        data = fetch_session_data(year, event, session_type)
        laps = data.get("laps")
        if laps is None or laps.empty:
            return {"success": False, "consistency": None}
            
        prof = DriverPerformanceEngine.compute_driver_consistency(laps, primary_driver)
        return sanitize_for_json({
            "success": True,
            "session_id": session_id,
            "primary_driver": primary_driver,
            "consistency": asdict(prof)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/driver-performance/ideal-lap")
def get_driver_performance_ideal_lap(
    session_id: str = "S-2024-SPAIN",
    primary_driver: str = "VER"
):
    try:
        from src.driver_performance_engine import DriverPerformanceEngine
        from src.data_ingestion import fetch_session_data
        from src.session_utils import parse_session_id
        
        year, event, session_type = parse_session_id(session_id)
        data = fetch_session_data(year, event, session_type)
        laps = data.get("laps")
        if laps is None or laps.empty:
            return {"success": False, "ideal_lap": None}
            
        ideal = DriverPerformanceEngine.reconstruct_ideal_lap(laps, primary_driver)
        return sanitize_for_json({
            "success": True,
            "session_id": session_id,
            "primary_driver": primary_driver,
            "ideal_lap": asdict(ideal)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/race-operations/timing-tower")
def get_race_operations_timing_tower(session_id: str = "S-2024-SPAIN"):
    try:
        from src.race_operations_service import RaceOperationsService
        tower = RaceOperationsService.get_timing_tower(session_id)
        return sanitize_for_json({
            "success": True,
            "session_id": session_id,
            "timing_tower": tower
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/race-operations/pit-stops")
def get_race_operations_pit_stops(session_id: str = "S-2024-SPAIN"):
    try:
        from src.race_operations_service import RaceOperationsService
        stops = RaceOperationsService.get_pit_stop_timeline(session_id)
        return sanitize_for_json({
            "success": True,
            "session_id": session_id,
            "pit_stops": stops
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/race-operations/race-control")
def get_race_operations_race_control(session_id: str = "S-2024-SPAIN"):
    try:
        from src.race_operations_service import RaceOperationsService
        events = RaceOperationsService.get_race_control_timeline(session_id)
        return sanitize_for_json({
            "success": True,
            "session_id": session_id,
            "race_control": events
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/race-operations/team-radio")
def get_race_operations_team_radio(session_id: str = "S-2024-SPAIN", driver_code: Optional[str] = None):
    try:
        from src.race_operations_service import RaceOperationsService
        radio = RaceOperationsService.get_team_radio_timeline(session_id, driver_code)
        return sanitize_for_json({
            "success": True,
            "session_id": session_id,
            "team_radio": radio
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/race-operations/regulations")
def get_race_operations_regulations():
    try:
        from src.race_operations_service import RaceOperationsService
        regs = RaceOperationsService.get_regulations_dossier()
        return sanitize_for_json({
            "success": True,
            "regulations": regs
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/historical/eras")
def get_historical_eras():
    try:
        from src.historical_intelligence_service import HistoricalIntelligenceService
        eras = HistoricalIntelligenceService.get_eras()
        return sanitize_for_json({
            "success": True,
            "eras": eras
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/historical/teammate-h2h")
def get_historical_teammate_h2h(season: int = 2024):
    try:
        from src.historical_intelligence_service import HistoricalIntelligenceService
        h2h = HistoricalIntelligenceService.get_teammate_head_to_head(season)
        return sanitize_for_json({
            "success": True,
            "season": season,
            "head_to_head": h2h
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/historical/championship-what-if")
def get_historical_championship_what_if(session_id: str = "S-2024-SPAIN"):
    try:
        from src.historical_intelligence_service import HistoricalIntelligenceService
        what_if = HistoricalIntelligenceService.calculate_championship_what_if(session_id)
        return sanitize_for_json({
            "success": True,
            "session_id": session_id,
            "what_if": what_if
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model-validation/benchmarks")
def get_model_validation_benchmarks():
    try:
        from src.model_validation_service import ModelValidationService
        benchmarks = ModelValidationService.get_benchmarks()
        calibration = ModelValidationService.get_calibration_curve()
        return sanitize_for_json({
            "success": True,
            "benchmarks": benchmarks,
            "calibration_curve": calibration
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# LIVE TELEMETRY & HISTORICAL REPLAY REAL-TIME PIPELINE ENDPOINTS
# =====================================================================
from src.live_telemetry_service import live_telemetry_service
from src.live_provider_factory import (
    get_live_provider,
    set_active_provider_mode,
    get_active_provider_mode,
    get_available_providers
)
from src.historical_replay_service import (
    historical_replay_service,
    historical_replay_provider
)
from fastapi import WebSocket, WebSocketDisconnect
import asyncio


class ReplayControlRequest(BaseModel):
    action: str  # "play", "start", "pause", "resume", "restart", "seek", "speed", "stop"
    year: Optional[int] = 2024
    event: Optional[str] = "Spanish Grand Prix"
    grand_prix: Optional[str] = None
    session_type: Optional[str] = "Race"
    driver_code: Optional[str] = None
    driver: Optional[str] = None
    speed: Optional[float] = None
    playback_speed: Optional[float] = None
    progress_pct: Optional[float] = None
    seek_index: Optional[int] = None
    lap_number: Optional[int] = None


class ProviderModeRequest(BaseModel):
    mode: str  # "LIVE" or "HISTORICAL_REPLAY"


@app.get("/api/live/providers")
def get_providers_list():
    """Returns available telemetry providers and current active mode."""
    return sanitize_for_json({
        "success": True,
        "active_mode": get_active_provider_mode(),
        "providers": get_available_providers()
    })


@app.post("/api/live/mode")
def set_provider_mode(req: ProviderModeRequest):
    """Sets active telemetry provider mode ('LIVE' or 'HISTORICAL_REPLAY')."""
    set_active_provider_mode(req.mode)
    return sanitize_for_json({
        "success": True,
        "active_mode": get_active_provider_mode()
    })


@app.get("/api/live/sessions")
def get_live_sessions(year: Optional[int] = None, mode: Optional[str] = None):
    try:
        provider = get_live_provider(mode=mode)
        sessions = provider.get_sessions(year=year)
        return sanitize_for_json({"success": True, "sessions": sessions})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/drivers")
def get_live_drivers(session_key: int, mode: Optional[str] = None):
    try:
        provider = get_live_provider(mode=mode)
        drivers = provider.get_session_drivers(session_key=session_key)
        return sanitize_for_json({"success": True, "drivers": drivers})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/telemetry/latest")
def get_latest_live_telemetry(session_key: int, driver_number: int, mode: Optional[str] = None):
    try:
        provider = get_live_provider(mode=mode)
        telemetry = provider.get_latest_telemetry(session_key=session_key, driver_number=driver_number)
        if not telemetry:
            return sanitize_for_json({"success": False, "message": "No telemetry found for driver/session", "data": None})
        return sanitize_for_json({"success": True, "data": telemetry})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/telemetry/history")
def get_live_telemetry_history(
    session_key: int,
    driver_number: int,
    limit: int = 50,
    since_timestamp: Optional[str] = None,
    mode: Optional[str] = None
):
    try:
        provider = get_live_provider(mode=mode)
        history = provider.get_telemetry_history(
            session_key=session_key,
            driver_number=driver_number,
            limit=limit,
            since_timestamp=since_timestamp
        )
        return sanitize_for_json({"success": True, "count": len(history), "history": history})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/telemetry/moving")
def get_moving_live_telemetry(session_key: int, driver_number: int, limit: int = 50, mode: Optional[str] = None):
    try:
        provider = get_live_provider(mode=mode)
        history = provider.get_telemetry_history(
            session_key=session_key,
            driver_number=driver_number,
            limit=limit
        )
        moving = [pt for pt in history if pt.get("speed_kmh") is not None and pt.get("speed_kmh", 0) >= 30.0]
        res = moving if moving else history
        return sanitize_for_json({"success": True, "count": len(res), "history": res})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/telemetry/test-stream")
def get_test_stream_telemetry(session_key: int, driver_number: int, step: int = 0):
    try:
        sample = live_telemetry_service.get_test_stream_point(
            session_key=session_key,
            driver_number=driver_number,
            index=step
        )
        return sanitize_for_json({"success": True, "data": sample})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/timing-tower")
def get_live_timing_tower(session_key: Optional[int] = None, mode: Optional[str] = None):
    try:
        provider = get_live_provider(mode=mode)
        tower = provider.get_timing_tower(session_key=session_key)
        return sanitize_for_json({"success": True, "count": len(tower), "tower": tower})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/weather")
def get_live_weather(session_key: Optional[int] = None, mode: Optional[str] = None):
    try:
        provider = get_live_provider(mode=mode)
        weather = provider.get_weather(session_key=session_key)
        return sanitize_for_json({"success": True, "weather": weather})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/race-control")
def get_live_race_control(session_key: Optional[int] = None, mode: Optional[str] = None):
    try:
        provider = get_live_provider(mode=mode)
        messages = provider.get_race_control_messages(session_key=session_key)
        return sanitize_for_json({"success": True, "count": len(messages), "messages": messages})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# Dedicated Historical Telemetry Replay Control & Discovery Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/replay/sessions")
def get_replay_available_sessions():
    """Discovers available cached historical sessions."""
    try:
        sessions = historical_replay_service.get_available_sessions()
        return sanitize_for_json({"success": True, "sessions": sessions})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/replay/drivers")
def get_replay_session_drivers(
    year: int = 2024,
    event: str = "Spanish Grand Prix",
    session_type: str = "Race"
):
    """Retrieves drivers participating in the selected historical session."""
    try:
        drivers = historical_replay_service.get_session_drivers(year=year, event=event, session_type=session_type)
        return sanitize_for_json({"success": True, "drivers": drivers})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/replay/control")
async def control_replay_playback(req: ReplayControlRequest):
    """
    Controls historical telemetry replay: play, pause, resume, restart, seek, speed, stop.
    """
    try:
        action = req.action.lower()
        if action in ["play", "start"]:
            target_event = req.event or req.grand_prix or "Spanish Grand Prix"
            target_driver = req.driver_code or req.driver or "VER"
            target_speed = req.speed if req.speed is not None else (req.playback_speed if req.playback_speed is not None else 1.0)
            ok = await historical_replay_service.start_replay(
                year=req.year or 2024,
                event=target_event,
                session_type=req.session_type or "Race",
                driver_code=target_driver,
                speed=target_speed,
                lap_number=req.lap_number
            )
            if not ok:
                return sanitize_for_json({
                    "success": False,
                    "error": historical_replay_service.recent_error or "Failed to start replay",
                    "status": historical_replay_service.get_replay_status()
                })
        elif action == "pause":
            historical_replay_service.pause()
        elif action == "resume":
            historical_replay_service.resume()
        elif action == "restart":
            historical_replay_service.restart()
        elif action == "seek":
            if req.progress_pct is not None:
                historical_replay_service.seek(req.progress_pct)
            elif req.seek_index is not None and historical_replay_service.total_samples > 0:
                pct = (req.seek_index / max(1, historical_replay_service.total_samples - 1)) * 100.0
                historical_replay_service.seek(pct)
        elif action == "speed":
            target_speed = req.speed if req.speed is not None else req.playback_speed
            if target_speed is not None:
                historical_replay_service.set_speed(target_speed)
        elif action == "stop":
            await historical_replay_service.stop_replay()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown replay action: {req.action}")

        status = historical_replay_service.get_replay_status()
        return sanitize_for_json({"success": True, "status": status})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/replay/status")
def get_replay_status():
    """Returns current replay status, speed, progress, and metadata."""
    try:
        return sanitize_for_json({
            "success": True,
            "status": historical_replay_service.get_replay_status()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/replay/telemetry/latest")
def get_replay_latest_telemetry():
    """Returns the latest streamed sample from the replay engine."""
    try:
        sample = historical_replay_service.get_latest_telemetry()
        return sanitize_for_json({
            "success": True,
            "available": sample is not None,
            "telemetry_status": "REPLAYING" if sample else "WAITING",
            "provenance": "HISTORICAL_REPLAY",
            "data_classification": "HISTORICAL_REPLAY",
            "sample": sample,
            "data": sample
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/replay/telemetry/history")
def get_replay_telemetry_history(limit: int = 50):
    """Returns recent history window of replayed telemetry samples."""
    try:
        history = historical_replay_service.get_telemetry_history(limit=limit)
        return sanitize_for_json({
            "success": True,
            "count": len(history),
            "provenance": "HISTORICAL_REPLAY",
            "history": history
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/replay/timing-tower")
def get_replay_timing_tower():
    """Returns timing tower for the historical replay session."""
    try:
        tower = historical_replay_service.get_timing_tower()
        return sanitize_for_json({
            "success": True,
            "count": len(tower),
            "provenance": "HISTORICAL_REPLAY",
            "rows": tower,
            "tower": tower
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/live/telemetry/{session_key}/{driver_number}")
async def websocket_live_telemetry(websocket: WebSocket, session_key: int, driver_number: int, mode: Optional[str] = "LIVE"):
    await websocket.accept()
    step = 0
    mode_upper = (mode or "LIVE").upper()
    try:
        if mode_upper in ["REPLAY", "HISTORICAL_REPLAY"]:
            # Streaming Historical Replay
            status = await asyncio.to_thread(historical_replay_service.get_replay_status)
            recent = await asyncio.to_thread(historical_replay_service.get_telemetry_history, 30)

            await websocket.send_json({
                "type": "INITIAL_SNAPSHOT",
                "mode": "HISTORICAL_REPLAY",
                "provenance": "HISTORICAL_REPLAY",
                "data_classification": "HISTORICAL_REPLAY",
                "replay_banner": "HISTORICAL REPLAY — NOT LIVE",
                "driver": status.get("driver") or str(driver_number),
                "sample": status.get("current_sample"),
                "status": status,
                "history": recent
            })

            last_sample_idx = status.get("current_index", -1)

            while True:
                rep_status = await asyncio.to_thread(historical_replay_service.get_replay_status)
                cur_idx = rep_status.get("current_index", -1)

                if cur_idx != last_sample_idx and rep_status.get("current_sample"):
                    last_sample_idx = cur_idx
                    await websocket.send_json({
                        "type": "TELEMETRY_UPDATE",
                        "mode": "HISTORICAL_REPLAY",
                        "provenance": "HISTORICAL_REPLAY",
                        "data_classification": "HISTORICAL_REPLAY",
                        "driver": rep_status.get("driver") or str(driver_number),
                        "sample": rep_status["current_sample"],
                        "data": rep_status["current_sample"],
                        "status": rep_status
                    })
                else:
                    await websocket.send_json({
                        "type": "REPLAY_HEARTBEAT",
                        "mode": "HISTORICAL_REPLAY",
                        "provenance": "HISTORICAL_REPLAY",
                        "data_classification": "HISTORICAL_REPLAY",
                        "driver": rep_status.get("driver") or str(driver_number),
                        "sample": rep_status.get("current_sample"),
                        "status": rep_status.get("state", "IDLE"),
                        "progress_pct": rep_status.get("progress_pct", 0.0),
                        "speed": rep_status.get("playback_speed", 1.0)
                    })

                step += 1
                await asyncio.sleep(0.1)  # 10Hz stream for smooth replay

        else:
            # LIVE or SIMULATOR Mode
            status = await asyncio.to_thread(live_telemetry_service.get_live_status)

            if mode_upper == "SIMULATOR":
                recent = await asyncio.to_thread(live_telemetry_service.get_moving_telemetry_history, session_key, driver_number, 30)
            else:
                recent = await asyncio.to_thread(live_telemetry_service.get_telemetry_history, session_key, driver_number, 30)

            await websocket.send_json({
                "type": "INITIAL_SNAPSHOT",
                "mode": mode_upper,
                "status": status,
                "history": recent
            })

            last_ts = recent[-1]["timestamp"] if recent else None

            while True:
                if step % 5 == 0:
                    status = await asyncio.to_thread(live_telemetry_service.get_live_status)

                if mode_upper == "SIMULATOR":
                    sample = live_telemetry_service.get_test_stream_point(session_key, driver_number, step)
                    step += 1
                    await websocket.send_json({"type": "TELEMETRY_UPDATE", "data": sample})
                else:
                    sample = await asyncio.to_thread(
                        live_telemetry_service.get_latest_telemetry,
                        session_key=session_key,
                        driver_number=driver_number
                    )
                    if sample and sample.get("car_telemetry_available"):
                        last_ts = sample.get("timestamp")
                        await websocket.send_json({"type": "TELEMETRY_UPDATE", "data": sample})
                    else:
                        heartbeat_status = status.get("session_status", "BETWEEN_SESSIONS")
                        await websocket.send_json({
                            "type": "HEARTBEAT",
                            "status": heartbeat_status,
                            "provider": status.get("provider", "F1 Live Timing SignalR")
                        })

                step += 1
                await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for session {session_key}, driver {driver_number}")
    except Exception as e:
        logger.error(f"WebSocket streaming error: {e}")


# Production SPA static file serving
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist'))
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't hijack API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

