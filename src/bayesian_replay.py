"""
Deterministic Race Replay & Zero Data-Leakage Backtesting Engine.
Replays a race lap-by-lap, updating Bayesian posteriors and rerunning Monte Carlo simulations.
Strictly prevents future-data leakage (Lap L evaluation ONLY sees telemetry up to Lap L).
"""

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

from bayesian_state import BayesianRaceState
from monte_carlo_engine import MonteCarloRaceEngine, StochasticSimulationOutcome
from race_state import CompleteRaceState, DriverState, TyreState, FuelState, WeatherState, TrackState, SafetyCarState
from strategy_model import ObjectiveType


class BayesianRaceReplayEngine:
    """
    Simulates sequential Bayesian state updates and strategy reruns over a full race replay.
    """

    @classmethod
    def replay_race_timeline(
        cls,
        session: Any,
        laps_df: pd.DataFrame,
        results_df: pd.DataFrame,
        target_driver: str,
        opponent_driver: str,
        step_laps: int = 5,
        mc_iterations: int = 2000
    ) -> Dict[str, Any]:
        """
        Replays race in step_laps increments without future-data leakage.
        """
        if laps_df.empty:
            return {"error": "Laps telemetry empty."}

        driver_laps = laps_df[laps_df['Driver'] == target_driver]
        if driver_laps.empty:
            return {"error": f"No laps for driver {target_driver}."}

        total_race_laps = int(driver_laps['LapNumber'].max())
        checkpoints = list(range(0, total_race_laps + 1, step_laps))
        if checkpoints[-1] != total_race_laps:
            checkpoints.append(total_race_laps)

        bayesian_state = BayesianRaceState(race_lap=0)
        mc_engine = MonteCarloRaceEngine(iterations=mc_iterations, seed=42)

        timeline = []

        for lap_step in checkpoints:
            # 1. Slice telemetry UP TO lap_step (STRICT ZERO DATA LEAKAGE)
            sliced_df = laps_df[laps_df['LapNumber'] <= lap_step].copy()

            # 2. Update Bayesian Race State
            bayesian_state.update_from_telemetry(sliced_df, target_driver, lap_step)
            b_snapshot = bayesian_state.get_snapshot(lap_step)

            # Extract Bayesian posterior tyre deg rate
            deg_param = bayesian_state.parameters.get("tyre_degradation")
            updated_deg_rate = deg_param.posterior_mean if deg_param else 0.07

            # Extract Bayesian posterior pace
            pace_param = bayesian_state.parameters.get("driver_pace")
            updated_pace = pace_param.posterior_mean if pace_param else 90.0

            # 3. Construct Race State for Monte Carlo Engine
            c_race_state = CompleteRaceState(
                current_lap=lap_step,
                total_laps=total_race_laps,
                drivers={},
                weather=WeatherState(track_temp_c=35.0),
                track=TrackState(track_name="Replay Circuit", total_laps=total_race_laps, pit_lane_loss_seconds=22.0),
                safety_car=SafetyCarState(sc_probability_per_lap=0.02)
            )

            # Determine position and actual compound at lap_step for target driver
            if lap_step > 0:
                drv_sliced = sliced_df[sliced_df['Driver'] == target_driver]
                step_lap_row = drv_sliced[drv_sliced['LapNumber'] == lap_step]
                if step_lap_row.empty and not drv_sliced.empty:
                    step_lap_row = drv_sliced.iloc[[-1]]
            else:
                step_lap_row = pd.DataFrame()

            t_pos = int(step_lap_row.iloc[0]['Position']) if not step_lap_row.empty and 'Position' in step_lap_row.columns and pd.notna(step_lap_row.iloc[0]['Position']) else 2
            t_tyre_age = int(step_lap_row.iloc[0]['TyreLife']) if not step_lap_row.empty and 'TyreLife' in step_lap_row.columns and pd.notna(step_lap_row.iloc[0]['TyreLife']) else lap_step
            t_compound = str(step_lap_row.iloc[0]['Compound']) if not step_lap_row.empty and 'Compound' in step_lap_row.columns and pd.notna(step_lap_row.iloc[0]['Compound']) else "MEDIUM"

            t_driver_state = DriverState(
                driver_id=target_driver,
                position=t_pos,
                current_gap_to_leader_s=0.0 if t_pos == 1 else 2.0,
                base_pace_s=updated_pace,
                tyre_state=TyreState(compound=t_compound, age_laps=t_tyre_age, remaining_grip_pct=80.0, thermal_deg_rate=updated_deg_rate),
                fuel_state=FuelState(fuel_remaining_kg=110.0 * (1.0 - (lap_step / total_race_laps)))
            )

            # Determine opponent driver state accurately
            opp_pos = 1 if t_pos > 1 else 2
            opp_tyre_age = lap_step
            opp_compound = "HARD"
            if lap_step > 0:
                opp_sliced = sliced_df[sliced_df['Driver'] == opponent_driver]
                opp_lap_row = opp_sliced[opp_sliced['LapNumber'] == lap_step]
                if opp_lap_row.empty and not opp_sliced.empty:
                    opp_lap_row = opp_sliced.iloc[[-1]]
                if not opp_lap_row.empty:
                    if 'Position' in opp_lap_row.columns and pd.notna(opp_lap_row.iloc[0]['Position']):
                        opp_pos = int(opp_lap_row.iloc[0]['Position'])
                    if 'TyreLife' in opp_lap_row.columns and pd.notna(opp_lap_row.iloc[0]['TyreLife']):
                        opp_tyre_age = int(opp_lap_row.iloc[0]['TyreLife'])
                    if 'Compound' in opp_lap_row.columns and pd.notna(opp_lap_row.iloc[0]['Compound']):
                        opp_compound = str(opp_lap_row.iloc[0]['Compound'])

            opponents = [
                DriverState(driver_id=opponent_driver, position=opp_pos, current_gap_to_leader_s=0.0 if opp_pos == 1 else 2.0, base_pace_s=updated_pace + 0.2, tyre_state=TyreState(opp_compound, opp_tyre_age, 80.0, 0.04), fuel_state=FuelState(60.0))
            ]

            # 4. Rerun Monte Carlo Simulation with Updated Bayesian Posteriors
            rankings = mc_engine.rank_strategies(t_driver_state, opponents, c_race_state, objective=ObjectiveType.MAX_PODIUM)
            best_strat = rankings[0] if rankings else None

            timeline.append({
                "race_lap": lap_step,
                "bayesian_snapshot": b_snapshot,
                "posterior_tyre_deg_s_per_lap": round(updated_deg_rate, 4),
                "posterior_pace_s": round(updated_pace, 3),
                "top_recommended_strategy": best_strat.strategy_plan.strategy_name if best_strat else "N/A",
                "simulated_win_prob_pct": round(best_strat.win_probability * 100.0, 1) if best_strat else 0.0,
                "simulated_podium_prob_pct": round(best_strat.podium_probability * 100.0, 1) if best_strat else 0.0,
                "expected_finish_position": best_strat.expected_position if best_strat else t_pos
            })

        return {
            "target_driver": target_driver,
            "total_laps": total_race_laps,
            "step_laps": step_laps,
            "checkpoints_count": len(checkpoints),
            "timeline": timeline,
            "bayesian_state": bayesian_state.to_dict()
        }
