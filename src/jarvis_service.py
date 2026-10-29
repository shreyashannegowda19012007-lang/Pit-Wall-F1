from src.data_providers import get_provider
from src.probabilistic_service import ProbabilisticService
from src.session_utils import parse_session_id, pick_driver_laps
import logging

logger = logging.getLogger(__name__)

class JarvisService:
    @staticmethod
    def generate_insights(session_id: str, primary_driver: str, ref_driver: str):
        year, event, session_type = parse_session_id(session_id)

        provider = get_provider()
        data = provider.fetch_session_data(year, event, session_type)
        if not data.get("success"):
            return {"success": False, "error": data.get("error", "Could not fetch session data.")}

        session = data.get("raw_session")
        if session is None:
            return {"success": False, "error": "Session object is null."}

        insights = []

        # 1. Basic Session Info
        insights.append({
            "category": "session",
            "message": f"[OBSERVED] Telemetry uplink synchronized for {year} {event} ({session_type}). Comparing {primary_driver} vs {ref_driver}."
        })

        p_median = None
        r_median = None

        # 2. Race Pace Insight
        try:
            laps = session.laps

            if laps is not None and not laps.empty:
                p_laps = pick_driver_laps(laps, primary_driver)
                r_laps = pick_driver_laps(laps, ref_driver)

                if not p_laps.empty and not r_laps.empty:
                    p_quick = p_laps.pick_quicklaps()
                    r_quick = r_laps.pick_quicklaps()

                    p_median = p_quick['LapTime'].dt.total_seconds().median() if not p_quick.empty else p_laps['LapTime'].dt.total_seconds().median()
                    r_median = r_quick['LapTime'].dt.total_seconds().median() if not r_quick.empty else r_laps['LapTime'].dt.total_seconds().median()

                    if p_median and r_median:
                        diff = p_median - r_median
                        if diff > 0.05:
                            insights.append({
                                "category": "pace",
                                "message": f"[OBSERVED] {primary_driver} median pace is {p_median:.3f}s vs {ref_driver} {r_median:.3f}s (+{diff:.3f}s deficit per lap)."
                            })
                        elif diff < -0.05:
                            insights.append({
                                "category": "pace",
                                "message": f"[OBSERVED] {primary_driver} holds a pace advantage of {abs(diff):.3f}s per lap over {ref_driver} ({p_median:.3f}s vs {r_median:.3f}s)."
                            })
                        else:
                            insights.append({
                                "category": "pace",
                                "message": f"[OBSERVED] {primary_driver} and {ref_driver} demonstrate closely matched median pace ({p_median:.3f}s vs {r_median:.3f}s)."
                            })
        except Exception as e:
            logger.debug(f"Jarvis pace error: {e}")

        # 3. Strategy Insight (Undercut/Overcut)
        try:
            laps = session.laps
            p_laps = pick_driver_laps(laps, primary_driver)
            r_laps = pick_driver_laps(laps, ref_driver)

            if not p_laps.empty and not r_laps.empty:
                common_lap = min(p_laps['LapNumber'].max(), r_laps['LapNumber'].max())
                p_lap = p_laps[p_laps['LapNumber'] == common_lap]
                r_lap = r_laps[r_laps['LapNumber'] == common_lap]

                gap_td = (p_lap['Time'].iloc[0] - r_lap['Time'].iloc[0]).total_seconds() if not p_lap.empty and not r_lap.empty else 2.0
                gap_s = abs(gap_td)
                primary_ahead = gap_td < 0

                strat = ProbabilisticService.analyze_undercut_overcut(
                    driver_id=primary_driver,
                    rival_driver_id=ref_driver,
                    gap_s=gap_s,
                    base_pace_s=p_median if p_median else 85.0,
                    rival_base_pace_s=r_median if r_median else 85.0,
                    primary_is_ahead=primary_ahead
                )
                rec = strat.get("tactic") or ("undercut" if "UNDERCUT" in strat.get("recommended_tactic", "") else ("overcut" if "OVERCUT" in strat.get("recommended_tactic", "") else "maintain"))

                if rec == "undercut":
                    prob = strat.get("undercut_success_probability_pct", 0)
                    gain = strat.get("undercut_expected_gain_s", 0)
                    insights.append({
                        "category": "strategy",
                        "message": f"[SIMULATED] Tactical advisory recommends an UNDERCUT against {ref_driver}. Current track gap: {gap_s:.2f}s (estimated net gain +{gain:.2f}s, win probability {prob:.1f}%)."
                    })
                elif rec == "overcut":
                    prob = strat.get("overcut_success_probability_pct", 0)
                    gain = strat.get("overcut_expected_gain_s", 0)
                    insights.append({
                        "category": "strategy",
                        "message": f"[SIMULATED] Tactical advisory recommends an OVERCUT against {ref_driver}. Current track gap: {gap_s:.2f}s (estimated net gain +{gain:.2f}s, win probability {prob:.1f}%). Extend stint."
                    })
                else:
                    insights.append({
                        "category": "strategy",
                        "message": f"[SIMULATED] Current track delta of {gap_s:.2f}s against {ref_driver} is outside the optimal pit delta window. Maintain track position and manage tyre thermal wear."
                    })
        except Exception as e:
            logger.debug(f"Jarvis strategy error: {e}")

        # 4. Tyre Insight
        try:
            from src.tyre_analytics import TyreAnalyticsEngine
            tyre_res = TyreAnalyticsEngine.analyze_stint_degradation(session, primary_driver)
            if tyre_res.get("success"):
                deg = tyre_res.get("degradation_slope_s_per_lap", 0)
                compound = tyre_res.get("compound", "Unknown")
                stint_num = tyre_res.get("stint_number", 1)
                r2 = tyre_res.get("r_squared", 0)

                if deg > 0.05:
                    insights.append({
                        "category": "tyres",
                        "message": f"[OBSERVED] {primary_driver} is experiencing linear thermal degradation of +{deg:.3f}s/lap on Stint {stint_num} ({compound} compound, R²={r2:.2f}). Approaching pit window."
                    })
                elif deg > 0:
                    insights.append({
                        "category": "tyres",
                        "message": f"[OBSERVED] {primary_driver} tyre degradation rate is stable at +{deg:.3f}s/lap on Stint {stint_num} ({compound} compound, R²={r2:.2f})."
                    })
                else:
                    insights.append({
                        "category": "tyres",
                        "message": f"[OBSERVED] {primary_driver} pace evolution on Stint {stint_num} ({compound} compound) shows track evolution offsetting tyre degradation ({deg:+.3f}s/lap)."
                    })
        except Exception as e:
            logger.debug(f"Jarvis tyre error: {e}")

        return {
            "success": True,
            "primary_driver": primary_driver,
            "reference_driver": ref_driver,
            "insights": insights
        }
