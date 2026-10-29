import pandas as pd
import numpy as np
from src.data_providers import get_provider
from src.telemetry_schema import DataStatus
from src.jarvis_service import JarvisService
from src.probabilistic_service import ProbabilisticService
from src.tyre_analytics import TyreAnalyticsEngine

class CommandCenterService:
    @staticmethod
    def get_command_center_data(session_id: str, primary_driver: str, ref_driver: str) -> dict:
        from src.session_utils import parse_session_id, pick_driver_laps
        year, event, session_type = parse_session_id(session_id)

        provider = get_provider()
        data = provider.fetch_session_data(year, event, session_type)

        if not data.get("success"):
            return {
                "success": False,
                "status": "UNAVAILABLE",
                "error": data.get("error", "Failed to load session data")
            }

        session = data.get("raw_session")
        if session is None:
            return {
                "success": False,
                "status": "UNAVAILABLE",
                "error": "Session object is null"
            }

        laps = session.laps
        results = session.results

        # Safe extraction of dataframe values
        def safe_get(df, col, default=None):
            if df is None or df.empty or col not in df.columns:
                return default
            val = df[col].iloc[0]
            if pd.isna(val):
                return default
            return val

        def get_driver_info(driver):
            drv_laps = pick_driver_laps(laps, driver)
            drv_res = results[results['Abbreviation'] == driver] if results is not None and 'Abbreviation' in results.columns else pd.DataFrame()
            
            if drv_laps.empty:
                return None
                
            last_lap_idx = drv_laps['LapNumber'].idxmax()
            last_lap = drv_laps.loc[[last_lap_idx]]
            
            quick_laps = drv_laps.pick_quicklaps()
            best_lap = quick_laps.loc[quick_laps['LapTime'].idxmin()] if not quick_laps.empty else None
            
            position = safe_get(drv_res, 'Position')
            if position is None:
                # Approximate position by looking at last lap position if available
                position = safe_get(last_lap, 'Position')

            last_lap_time = safe_get(last_lap, 'LapTime')
            best_lap_time = best_lap['LapTime'] if best_lap is not None else None
            
            # Sectors
            s1 = safe_get(last_lap, 'Sector1Time')
            s2 = safe_get(last_lap, 'Sector2Time')
            s3 = safe_get(last_lap, 'Sector3Time')

            return {
                "position": int(position) if position is not None else None,
                "current_lap": int(safe_get(last_lap, 'LapNumber', 0)),
                "tyre_compound": safe_get(last_lap, 'Compound', 'UNKNOWN'),
                "tyre_age": int(safe_get(last_lap, 'TyreLife', 0)),
                "last_lap_time": last_lap_time.total_seconds() if pd.notna(last_lap_time) else None,
                "best_lap_time": best_lap_time.total_seconds() if pd.notna(best_lap_time) else None,
                "sector_1": s1.total_seconds() if pd.notna(s1) else None,
                "sector_2": s2.total_seconds() if pd.notna(s2) else None,
                "sector_3": s3.total_seconds() if pd.notna(s3) else None,
                "pit_status": safe_get(last_lap, 'PitOutTime') is not None or safe_get(last_lap, 'PitInTime') is not None,
                "laps_df": drv_laps
            }

        primary_info = get_driver_info(primary_driver)
        ref_info = get_driver_info(ref_driver)

        if not primary_info:
            return {"success": False, "error": f"No laps found for primary driver {primary_driver}"}
        
        # Calculate Gaps
        # A simple track gap calculation based on the last completed common lap
        gap_ahead = None
        gap_behind = None
        ref_gap = None
        common_lap = None

        if ref_info:
            common_lap = min(primary_info['current_lap'], ref_info['current_lap'])
            if common_lap > 0:
                p_lap = primary_info['laps_df'][primary_info['laps_df']['LapNumber'] == common_lap]
                r_lap = ref_info['laps_df'][ref_info['laps_df']['LapNumber'] == common_lap]
                if not p_lap.empty and not r_lap.empty:
                    gap_td = p_lap['Time'].iloc[0] - r_lap['Time'].iloc[0]
                    ref_gap = gap_td.total_seconds()

        # Strategy and Tyre degradation
        primary_tyre_res = TyreAnalyticsEngine.analyze_stint_degradation(session, primary_driver)
        ref_tyre_res = TyreAnalyticsEngine.analyze_stint_degradation(session, ref_driver) if ref_info else {}

        # Pace calculations
        primary_pace_avg = None
        if not primary_info['laps_df'].empty:
            recent_laps = primary_info['laps_df'].tail(5)
            # filter out pit laps
            recent_laps = recent_laps[pd.isna(recent_laps['PitInTime']) & pd.isna(recent_laps['PitOutTime'])]
            if not recent_laps.empty:
                primary_pace_avg = recent_laps['LapTime'].dt.total_seconds().mean()

        ref_pace_avg = None
        if ref_info and not ref_info['laps_df'].empty:
            recent_laps = ref_info['laps_df'].tail(5)
            recent_laps = recent_laps[pd.isna(recent_laps['PitInTime']) & pd.isna(recent_laps['PitOutTime'])]
            if not recent_laps.empty:
                ref_pace_avg = recent_laps['LapTime'].dt.total_seconds().mean()

        # Jarvis Insights
        jarvis_res = JarvisService.generate_insights(session_id, primary_driver, ref_driver)
        jarvis_summary = jarvis_res.get('insights', []) if isinstance(jarvis_res, dict) else []

        # Strategy Simulation
        strategy_res = {}
        if ref_info and ref_gap is not None and primary_pace_avg is not None and ref_pace_avg is not None:
            strat = ProbabilisticService.analyze_undercut_overcut(
                primary_driver, ref_driver, abs(ref_gap), primary_pace_avg, ref_pace_avg
            )
            if strat.get("success"):
                strategy_res = {
                    "undercut_opportunity": strat.get("undercut_success_probability_pct", 0) > 50,
                    "overcut_opportunity": strat.get("overcut_success_probability_pct", 0) > 50,
                    "recommendation": strat.get("recommended_tactic", "MAINTAIN"),
                    "confidence": max(strat.get("undercut_success_probability_pct", 0), strat.get("overcut_success_probability_pct", 0))
                }

        # Build final payload
        payload = {
            "success": True,
            "session": {
                "name": f"{year} {event}",
                "type": session.session_info['Type'] if 'Type' in session.session_info else 'Race',
                "date": str(session.session_info['StartDate']) if 'StartDate' in session.session_info else '',
                "current_lap": primary_info['current_lap'],
                "total_laps": session.total_laps if hasattr(session, 'total_laps') else None,
            },
            "primary_driver": {
                "id": primary_driver,
                "position": primary_info['position'],
                "current_lap": primary_info['current_lap'],
                "last_lap_time": primary_info['last_lap_time'],
                "best_lap_time": primary_info['best_lap_time'],
                "sector_1": primary_info['sector_1'],
                "sector_2": primary_info['sector_2'],
                "sector_3": primary_info['sector_3'],
                "pit_status": primary_info['pit_status']
            },
            "reference_driver": {
                "id": ref_driver,
                "position": ref_info['position'] if ref_info else None,
                "gap": ref_gap,
                "current_lap": ref_info['current_lap'] if ref_info else None,
            } if ref_info else None,
            "tyres": {
                "primary": {
                    "compound": primary_info['tyre_compound'],
                    "age": primary_info['tyre_age'],
                    "estimated_degradation": primary_tyre_res.get('degradation_slope_s_per_lap') or primary_tyre_res.get('estimated_degradation_per_lap') if isinstance(primary_tyre_res, dict) else None
                },
                "reference": {
                    "compound": ref_info['tyre_compound'],
                    "age": ref_info['tyre_age'],
                    "estimated_degradation": ref_tyre_res.get('degradation_slope_s_per_lap') or ref_tyre_res.get('estimated_degradation_per_lap') if isinstance(ref_tyre_res, dict) else None
                } if ref_info else None
            },
            "pace": {
                "primary_rolling_avg": primary_pace_avg,
                "reference_rolling_avg": ref_pace_avg,
                "delta": (primary_pace_avg - ref_pace_avg) if (primary_pace_avg and ref_pace_avg) else None
            },
            "strategy": strategy_res,
            "jarvis": {
                "summary": jarvis_summary
            },
            "race_control": {
                "track_status": session.track_status['Status'].iloc[-1] if hasattr(session, 'track_status') and session.track_status is not None and not session.track_status.empty and 'Status' in session.track_status.columns else "1"
            },
            "changes": [
                f"Command Center initialized for {primary_driver}"
            ]
        }
        
        return payload
