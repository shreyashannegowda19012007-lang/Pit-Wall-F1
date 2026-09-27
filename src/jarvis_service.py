from src.data_providers import get_provider
from src.probabilistic_service import ProbabilisticService

class JarvisService:
    @staticmethod
    def generate_insights(session_id: str, primary_driver: str, ref_driver: str):
        parts = session_id.split('-')
        year = int(parts[1]) if len(parts) > 1 else 2024
        event = parts[2] if len(parts) > 2 else "SPAIN"

        provider = get_provider()
        data = provider.fetch_session_data(year, event, 'R')
        if not data.get("success"):
            return {"success": False, "error": "Could not fetch session data."}

        session = data["raw_session"]

        insights = []

        # 1. Basic Session Info
        insights.append({
            "category": "session",
            "message": f"Analyzing {year} {event} Grand Prix."
        })

        # 2. Race Pace Insight
        try:
            laps = session.laps

            if not hasattr(laps, 'pick_drivers') and not hasattr(laps, 'pick_driver'):
                return {"success": False, "error": "Invalid session lap structure."}

            p_laps = laps.pick_driver(primary_driver)
            r_laps = laps.pick_driver(ref_driver)

            if p_laps.empty:
                return {"success": False, "error": f"No lap data found for driver {primary_driver}."}
            if r_laps.empty:
                return {"success": False, "error": f"No lap data found for driver {ref_driver}."}

            p_quick = p_laps.pick_quicklaps()
            r_quick = r_laps.pick_quicklaps()

            p_median = p_quick['LapTime'].dt.total_seconds().median()
            r_median = r_quick['LapTime'].dt.total_seconds().median()

            if p_median and r_median:
                diff = p_median - r_median
                if diff > 0.1:
                    insights.append({
                        "category": "pace",
                        "message": f"{primary_driver} is structurally slower than {ref_driver} by {abs(diff):.2f}s per lap on average."
                    })
                elif diff < -0.1:
                    insights.append({
                        "category": "pace",
                        "message": f"{primary_driver} is structurally faster than {ref_driver} by {abs(diff):.2f}s per lap on average."
                    })
                else:
                    insights.append({
                        "category": "pace",
                        "message": f"Both {primary_driver} and {ref_driver} are showing identical race pace."
                    })
        except Exception as e:
            pass

        # 3. Strategy Insight (Undercut/Overcut)
        try:
            primary_laps = laps.pick_driver(primary_driver)
            ref_laps = laps.pick_driver(ref_driver)

            common_lap = min(primary_laps['LapNumber'].max(), ref_laps['LapNumber'].max())
            p_lap = primary_laps[primary_laps['LapNumber'] == common_lap]
            r_lap = ref_laps[ref_laps['LapNumber'] == common_lap]

            gap_s = abs((p_lap['Time'].iloc[0] - r_lap['Time'].iloc[0]).total_seconds()) if not p_lap.empty and not r_lap.empty else 2.0

            strat = ProbabilisticService.analyze_undercut_overcut(primary_driver, ref_driver, gap_s, p_median if p_median else 85.0)
            rec = strat.get("recommended_tactic")
            if rec == "undercut":
                prob = strat.get("undercut_success_probability_pct", 0)
                insights.append({
                    "category": "strategy",
                    "message": f"JARVIS recommends an UNDERCUT against {ref_driver}. With a track gap of {gap_s:.1f}s, the current Monte Carlo probability of success is {prob:.1f}%."
                })
            elif rec == "overcut":
                prob = strat.get("overcut_success_probability_pct", 0)
                insights.append({
                    "category": "strategy",
                    "message": f"JARVIS recommends an OVERCUT against {ref_driver}. With a track gap of {gap_s:.1f}s, the probability of success is {prob:.1f}%. Avoid pitting early."
                })
            else:
                insights.append({
                    "category": "strategy",
                    "message": f"Neither undercut nor overcut shows high viability against {ref_driver} at the current gap of {gap_s:.1f}s. Maintain track position."
                })
        except Exception:
            pass

        # 4. Tyre Insight
        try:
            from src.tyre_analytics import TyreAnalyticsEngine
            tyre_res = TyreAnalyticsEngine.analyze_stint_degradation(session, primary_driver)
            if tyre_res.get("stints"):
                last_stint = tyre_res["stints"][-1]
                deg = last_stint.get("degradation_slope", 0)
                if deg > 0.05:
                    insights.append({
                        "category": "tyres",
                        "message": f"{primary_driver} is experiencing HIGH tyre degradation ({deg:.3f}s/lap) on the current {last_stint.get('compound', 'Unknown')} compound stint. Manage slip angles."
                    })
                elif deg > 0:
                    insights.append({
                        "category": "tyres",
                        "message": f"{primary_driver} is showing normal tyre degradation ({deg:.3f}s/lap) on the {last_stint.get('compound', 'Unknown')} compound."
                    })
        except Exception:
            pass

        return {
            "success": True,
            "primary_driver": primary_driver,
            "reference_driver": ref_driver,
            "insights": insights
        }
