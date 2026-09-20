"""
Sensitivity Analysis Engine for F1 Monte Carlo Strategy Simulator.
Calculates the relative impact of uncertain input variables (Tyre Deg, SC Risk, Pit Loss, Traffic)
on strategy win and podium probabilities via OAT (One-At-a-Time) parameter perturbation.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import copy

from race_state import CompleteRaceState, DriverState
from strategy_model import StrategyPlan
from monte_carlo_engine import MonteCarloRaceEngine


class SensitivityAnalysisEngine:
    """
    Computes global & OAT parameter sensitivity rankings.
    """

    @classmethod
    def _clone_scenario_context(
        cls,
        target_driver: DriverState,
        opponents: List[DriverState],
        race_state: CompleteRaceState
    ) -> Tuple[DriverState, List[DriverState], CompleteRaceState]:
        """
        Creates a deepcopy of race state and retrieves/binds cloned driver instances
        to ensure all in-place parameter perturbations propagate strictly to the simulation.
        """
        state_clone = copy.deepcopy(race_state)

        # Locate or place target driver inside cloned state
        if target_driver.driver_id in state_clone.drivers:
            cloned_target = state_clone.drivers[target_driver.driver_id]
        else:
            cloned_target = copy.deepcopy(target_driver)
            state_clone.drivers[cloned_target.driver_id] = cloned_target

        # Locate or place opponents inside cloned state
        cloned_opponents = []
        for opp in opponents:
            if opp.driver_id in state_clone.drivers:
                cloned_opponents.append(state_clone.drivers[opp.driver_id])
            else:
                cloned_opp = copy.deepcopy(opp)
                state_clone.drivers[cloned_opp.driver_id] = cloned_opp
                cloned_opponents.append(cloned_opp)

        return cloned_target, cloned_opponents, state_clone

    @classmethod
    def evaluate_sensitivity(
        cls,
        strategy: StrategyPlan,
        target_driver: DriverState,
        opponents: List[DriverState],
        race_state: CompleteRaceState,
        iterations: int = 2000
    ) -> Dict[str, Any]:
        """
        Perturbs key uncertain parameters and measures output shifts across
        podium probability, win probability, expected finish position, and race time.
        """
        engine = MonteCarloRaceEngine(iterations=iterations, seed=42)

        # Baseline Evaluation (using cloned context for reference purity)
        b_target, b_opps, b_state = cls._clone_scenario_context(target_driver, opponents, race_state)
        base_res = engine.simulate_strategy_vectorized(strategy, b_target, b_opps, b_state)
        base_podium = base_res.podium_probability
        base_win = base_res.win_probability
        base_time = base_res.expected_race_time_min

        scenario_outcomes = {"baseline": base_res}

        # 1. Tyre Degradation Perturbations (-10%, +10%, +20%)
        # Deg -10%
        t_target_m10, t_opps_m10, t_state_m10 = cls._clone_scenario_context(target_driver, opponents, race_state)
        t_target_m10.tyre_degradation_rate *= 0.9
        for drv in t_opps_m10:
            drv.tyre_degradation_rate *= 0.9
        deg_low_res = engine.run_simulation(strategy, t_target_m10, t_opps_m10, t_state_m10)
        scenario_outcomes["tyre_deg_low"] = deg_low_res

        # Deg +10%
        t_target_p10, t_opps_p10, t_state_p10 = cls._clone_scenario_context(target_driver, opponents, race_state)
        t_target_p10.tyre_degradation_rate *= 1.1
        for drv in t_opps_p10:
            drv.tyre_degradation_rate *= 1.1
        deg_high_res = engine.run_simulation(strategy, t_target_p10, t_opps_p10, t_state_p10)
        scenario_outcomes["tyre_deg_high"] = deg_high_res

        # Deg +20%
        t_target_p20, t_opps_p20, t_state_p20 = cls._clone_scenario_context(target_driver, opponents, race_state)
        t_target_p20.tyre_degradation_rate *= 1.2
        for drv in t_opps_p20:
            drv.tyre_degradation_rate *= 1.2
        deg_p20_res = engine.run_simulation(strategy, t_target_p20, t_opps_p20, t_state_p20)
        scenario_outcomes["tyre_deg_p20"] = deg_p20_res

        # 2. Pit Loss Perturbations (-10%, +10%)
        # Pit Loss -10%
        p_target_low, p_opps_low, p_state_low = cls._clone_scenario_context(target_driver, opponents, race_state)
        p_state_low.track.pit_lane_loss_seconds *= 0.9
        pit_low_res = engine.run_simulation(strategy, p_target_low, p_opps_low, p_state_low)
        scenario_outcomes["pit_loss_low"] = pit_low_res

        # Pit Loss +10%
        p_target_high, p_opps_high, p_state_high = cls._clone_scenario_context(target_driver, opponents, race_state)
        p_state_high.track.pit_lane_loss_seconds *= 1.1
        pit_high_res = engine.run_simulation(strategy, p_target_high, p_opps_high, p_state_high)
        scenario_outcomes["pit_loss_high"] = pit_high_res

        # 3. Pace Perturbations (-10% pace improvement / +10% pace deficit)
        # Pace -10% (faster pace, lower lap time)
        pace_target_low, pace_opps_low, pace_state_low = cls._clone_scenario_context(target_driver, opponents, race_state)
        pace_target_low.base_pace_s *= 0.90
        pace_low_res = engine.run_simulation(strategy, pace_target_low, pace_opps_low, pace_state_low)
        scenario_outcomes["pace_low"] = pace_low_res

        # Pace +10% (slower pace, higher lap time)
        pace_target_high, pace_opps_high, pace_state_high = cls._clone_scenario_context(target_driver, opponents, race_state)
        pace_target_high.base_pace_s *= 1.10
        pace_high_res = engine.run_simulation(strategy, pace_target_high, pace_opps_high, pace_state_high)
        scenario_outcomes["pace_high"] = pace_high_res

        # 4. Safety Car Risk (+50%)
        sc_target, sc_opps, sc_state = cls._clone_scenario_context(target_driver, opponents, race_state)
        sc_state.safety_car.sc_probability_per_lap *= 1.5
        sc_res = engine.run_simulation(strategy, sc_target, sc_opps, sc_state)
        scenario_outcomes["sc_high"] = sc_res

        # 5. Fuel Effect (+20% penalty per kg)
        fuel_target, fuel_opps, fuel_state = cls._clone_scenario_context(target_driver, opponents, race_state)
        if hasattr(fuel_target, "fuel_state") and fuel_target.fuel_state is not None:
            fuel_target.fuel_state.fuel_time_penalty_per_kg *= 1.2
        for drv in fuel_opps:
            if hasattr(drv, "fuel_state") and drv.fuel_state is not None:
                drv.fuel_state.fuel_time_penalty_per_kg *= 1.2
        fuel_res = engine.run_simulation(strategy, fuel_target, fuel_opps, fuel_state)
        scenario_outcomes["fuel_effect_high"] = fuel_res

        # 6. Track Evolution (+50% grip progression)
        evo_target, evo_opps, evo_state = cls._clone_scenario_context(target_driver, opponents, race_state)
        evo_state.track.track_evolution_factor = min(1.0, evo_state.track.track_evolution_factor * 1.5)
        evo_res = engine.run_simulation(strategy, evo_target, evo_opps, evo_state)
        scenario_outcomes["track_evolution_high"] = evo_res

        # Calculate impacts
        tyre_impact = max(
            abs(deg_p20_res.podium_probability - base_podium),
            abs(deg_high_res.podium_probability - base_podium),
            abs(deg_low_res.podium_probability - base_podium),
            abs(deg_p20_res.expected_race_time_min - base_time) / max(1.0, base_time)
        )
        pit_impact = max(
            abs(pit_high_res.podium_probability - base_podium),
            abs(pit_low_res.podium_probability - base_podium),
            abs(pit_high_res.expected_race_time_min - base_time) / max(1.0, base_time)
        )
        sc_impact = abs(sc_res.podium_probability - base_podium)
        pace_impact = max(
            abs(pace_high_res.podium_probability - base_podium),
            abs(pace_low_res.podium_probability - base_podium),
            abs(pace_high_res.expected_race_time_min - base_time) / max(1.0, base_time)
        )
        fuel_impact = max(
            abs(fuel_res.podium_probability - base_podium),
            abs(fuel_res.expected_race_time_min - base_time) / max(1.0, base_time)
        )
        evo_impact = max(
            abs(evo_res.podium_probability - base_podium),
            abs(evo_res.expected_race_time_min - base_time) / max(1.0, base_time)
        )

        sens_factors = [
            {
                "factor": "Tyre Thermal Degradation",
                "relative_impact": "HIGH" if tyre_impact > 0.05 else ("MEDIUM" if tyre_impact > 0.02 else "LOW"),
                "podium_delta_pct": round(abs(deg_p20_res.podium_probability - base_podium) * 100.0, 1),
                "time_delta_s": round((deg_p20_res.expected_race_time_min - base_time) * 60.0, 2)
            },
            {
                "factor": "Safety Car / VSC Timing",
                "relative_impact": "HIGH" if sc_impact > 0.05 else ("MEDIUM" if sc_impact > 0.02 else "LOW"),
                "podium_delta_pct": round(sc_impact * 100.0, 1),
                "time_delta_s": round((sc_res.expected_race_time_min - base_time) * 60.0, 2)
            },
            {
                "factor": "Pit Stop Travel Loss",
                "relative_impact": "HIGH" if pit_impact > 0.05 else ("MEDIUM" if pit_impact > 0.02 else "LOW"),
                "podium_delta_pct": round(abs(pit_high_res.podium_probability - base_podium) * 100.0, 1),
                "time_delta_s": round((pit_high_res.expected_race_time_min - base_time) * 60.0, 2)
            },
            {
                "factor": "Fuel Effect Sensitivity",
                "relative_impact": "HIGH" if fuel_impact > 0.05 else ("MEDIUM" if fuel_impact > 0.02 else "LOW"),
                "podium_delta_pct": round(abs(fuel_res.podium_probability - base_podium) * 100.0, 1),
                "time_delta_s": round((fuel_res.expected_race_time_min - base_time) * 60.0, 2)
            },
            {
                "factor": "Track Evolution Rate",
                "relative_impact": "HIGH" if evo_impact > 0.05 else ("MEDIUM" if evo_impact > 0.02 else "LOW"),
                "podium_delta_pct": round(abs(evo_res.podium_probability - base_podium) * 100.0, 1),
                "time_delta_s": round((evo_res.expected_race_time_min - base_time) * 60.0, 2)
            }
        ]

        sens_factors.sort(key=lambda x: (x["podium_delta_pct"], abs(x["time_delta_s"])), reverse=True)

        return {
            "strategy_name": strategy.strategy_name,
            "baseline_podium_pct": round(base_podium * 100.0, 1),
            "baseline_win_pct": round(base_win * 100.0, 1),
            "baseline_time_min": round(base_time, 2),
            "top_uncertainty_driver": sens_factors[0]["factor"],
            "sensitivity_factors": sens_factors,
            "scenario_results": {
                k: {
                    "podium_probability": v.podium_probability,
                    "win_probability": v.win_probability,
                    "expected_position": v.expected_position,
                    "expected_race_time_min": v.expected_race_time_min,
                    "delta_podium_pct": round((v.podium_probability - base_podium) * 100.0, 1),
                    "delta_time_s": round((v.expected_race_time_min - base_time) * 60.0, 2)
                }
                for k, v in scenario_outcomes.items()
            }
        }

