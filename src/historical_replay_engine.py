"""
Chronological Historical Race Replay & Counterfactual Simulation Engine.
Replays historical races step-by-step with programmatic zero future-data leakage enforcement.
Evaluates model strategy choices against actual historical team decisions and hindsight oracles.
"""

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

from historical_leakage_guard import HistoricalInformationFilter, DataLeakageError
from historical_metrics import HistoricalReplayMetrics
from bayesian_state import BayesianRaceState
from monte_carlo_engine import MonteCarloRaceEngine
from decision_engine import DecisionEngine, ObjectiveType
from race_state import CompleteRaceState, DriverState, TyreState, FuelState, WeatherState, TrackState, SafetyCarState


class HistoricalReplayEngine:
    """
    Executes full historical race replay, recording model recommendations vs actual team decisions.
    """

    @classmethod
    def run_full_race_replay(
        cls,
        session: Any,
        laps_df: pd.DataFrame,
        results_df: pd.DataFrame,
        target_driver: str,
        opponent_driver: str = "HAM",
        step_laps: int = 5,
        mc_iterations: int = 1500,
        decision_lap: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes chronological backtest replay with strict leakage prevention.
        """
        if laps_df.empty:
            return {"error": "Telemetry laps dataset is empty."}

        info_filter = HistoricalInformationFilter(laps_df, session)
        driver_laps = laps_df[laps_df['Driver'] == target_driver]
        if driver_laps.empty:
            return {"error": f"No laps found for driver {target_driver}."}

        total_race_laps = int(driver_laps['LapNumber'].max())
        if decision_lap is not None:
            checkpoints = [decision_lap]
        else:
            checkpoints = list(range(0, total_race_laps + 1, step_laps))
            if checkpoints[-1] != total_race_laps:
                checkpoints.append(total_race_laps)

        # Actual Final Finishing Position from results_df if available
        actual_final_pos = None
        if results_df is not None and not results_df.empty and 'Abbreviation' in results_df.columns:
            res_row = results_df[results_df['Abbreviation'] == target_driver]
            if not res_row.empty and 'Position' in res_row.columns and pd.notna(res_row.iloc[0]['Position']):
                actual_final_pos = float(res_row.iloc[0]['Position'])

        # Hindsight Oracle benchmark must not be synthetically calculated.
        # Mark as None to indicate an Exact Offline Solver is required.
        hindsight_best_pos = None

        bayesian_state = BayesianRaceState(race_lap=0)
        mc_engine = MonteCarloRaceEngine(iterations=mc_iterations, seed=42)

        checkpoint_records = []

        for lap_step in checkpoints:
            # 1. Programmatically slice telemetry UP TO lap_step (STRICT ZERO FUTURE DATA LEAKAGE)
            sliced_df = info_filter.get_sliced_laps(lap_step)
            info_filter.validate_dataframe_sliced(sliced_df, lap_step, f"Replay Lap {lap_step}")

            # 2. Update Bayesian Race State using ONLY sliced_df
            bayesian_state.update_from_telemetry(sliced_df, target_driver, lap_step)
            b_snapshot = bayesian_state.get_snapshot(lap_step)

            deg_param = bayesian_state.parameters.get("tyre_degradation")
            updated_deg_rate = deg_param.posterior_mean if deg_param else 0.07

            pace_param = bayesian_state.parameters.get("driver_pace")
            updated_pace = pace_param.posterior_mean if pace_param else 90.0

            # 3. Construct CompleteRaceState
            c_race_state = CompleteRaceState(
                current_lap=lap_step,
                total_laps=total_race_laps,
                drivers={},
                weather=WeatherState(track_temp_c=35.0),
                track=TrackState("Historical Circuit", total_race_laps, 22.0),
                safety_car=SafetyCarState("GREEN", 0.02)
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

            # 4. Rerun Monte Carlo Engine & Decision Engine
            rankings = mc_engine.rank_strategies(t_driver_state, opponents, c_race_state, objective=ObjectiveType.MAX_PODIUM)
            struct_decision = DecisionEngine.evaluate(c_race_state, bayesian_state, rankings, objective=ObjectiveType.MAX_PODIUM)

            # Determine actual historical action taken by team at lap_step
            actual_action = "PIT" if not step_lap_row.empty and t_tyre_age == 1 and lap_step > 1 else "STAY_OUT"

            checkpoint_records.append({
                "race_lap": lap_step,
                "model_recommendation": struct_decision.selected_strategy_name,
                "recommended_action": struct_decision.recommended_action,
                "actual_team_action": actual_action,
                "model_expected_finish": struct_decision.expected_finish,
                "model_win_prob_pct": struct_decision.win_probability_pct,
                "model_podium_prob_pct": struct_decision.podium_probability_pct,
                "posterior_tyre_deg": round(updated_deg_rate, 4),
                "decision_payload": struct_decision.to_dict()
            })

        # 5. Calculate Backtest Summary Metrics
        summary_metrics = HistoricalReplayMetrics.evaluate_replay_summary(
            checkpoint_records,
            actual_final_finish=actual_final_pos,
            hindsight_best_finish=hindsight_best_pos
        )

        return {
            "target_driver": target_driver,
            "total_laps": total_race_laps,
            "checkpoints": checkpoint_records,
            "summary_metrics": summary_metrics,
            "data_leakage_protected": True
        }
