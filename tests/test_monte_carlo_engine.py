"""
Automated Unit Test & Performance Benchmark Suite for Monte Carlo Stochastic Race Engine.
Verifies seed reproducibility, multi-stint simulation, probability vector invariants,
multi-objective ranking, sensitivity analysis, scenario presets, and 10k-100k performance benchmarks.
"""

import unittest
import numpy as np
import time
import os
import sys

sys.path.insert(0, os.path.abspath('src'))

from race_state import CompleteRaceState, DriverState, TyreState, FuelState, WeatherState, TrackState, SafetyCarState
from strategy_model import StrategyPlan, StintPlan, ObjectiveType
from monte_carlo_engine import MonteCarloRaceEngine, StochasticSimulationOutcome
from sensitivity_analysis import SensitivityAnalysisEngine
from scenario_engine import ScenarioEngine, ScenarioPreset
from probabilistic_model import validate_probability_vector


class TestMonteCarloRaceEngine(unittest.TestCase):

    def setUp(self):
        self.driver_target = DriverState(
            driver_id="VER",
            position=2,
            current_gap_to_leader_s=1.5,
            base_pace_s=85.0,
            tyre_state=TyreState(compound="MEDIUM", age_laps=10, remaining_grip_pct=80.0, thermal_deg_rate=0.07),
            fuel_state=FuelState(fuel_remaining_kg=60.0)
        )

        self.opponents = [
            DriverState("NOR", position=1, current_gap_to_leader_s=0.0, base_pace_s=84.9, tyre_state=TyreState("HARD", 12, 85.0, 0.04), fuel_state=FuelState(60.0)),
            DriverState("LEC", position=3, current_gap_to_leader_s=4.0, base_pace_s=85.2, tyre_state=TyreState("MEDIUM", 10, 78.0, 0.07), fuel_state=FuelState(60.0))
        ]

        self.race_state = CompleteRaceState(
            current_lap=15,
            total_laps=50,
            drivers={"VER": self.driver_target},
            weather=WeatherState(condition="DRY", track_temp_c=35.0),
            track=TrackState(track_name="Spain", total_laps=50, pit_lane_loss_seconds=22.0),
            safety_car=SafetyCarState(condition="GREEN", sc_probability_per_lap=0.02)
        )

    def test_seed_reproducibility(self):
        """Verifies that a fixed seed produces identical simulation outcomes across runs."""
        strat = StrategyPlan("1-Stop (Hard)", [StintPlan("MEDIUM", 15, 25), StintPlan("HARD", 25, 50)], [25], ["MEDIUM", "HARD"], 1)

        engine1 = MonteCarloRaceEngine(iterations=2000, seed=42)
        out1 = engine1.simulate_strategy_vectorized(strat, self.driver_target, self.opponents, self.race_state)

        engine2 = MonteCarloRaceEngine(iterations=2000, seed=42)
        out2 = engine2.simulate_strategy_vectorized(strat, self.driver_target, self.opponents, self.race_state)

        self.assertAlmostEqual(out1.expected_position, out2.expected_position, places=4)
        self.assertAlmostEqual(out1.win_probability, out2.win_probability, places=4)
        self.assertAlmostEqual(out1.expected_race_time_min, out2.expected_race_time_min, places=4)

    def test_probability_vector_invariants(self):
        """Verifies discrete position probability map sums to 1.0 and contains no negative values."""
        strat = StrategyPlan("1-Stop (Hard)", [StintPlan("MEDIUM", 15, 25), StintPlan("HARD", 25, 50)], [25], ["MEDIUM", "HARD"], 1)
        engine = MonteCarloRaceEngine(iterations=3000, seed=42)
        out = engine.simulate_strategy_vectorized(strat, self.driver_target, self.opponents, self.race_state)

        probs_map = out.probabilities_map
        is_valid, total_sum = validate_probability_vector(probs_map)
        self.assertTrue(is_valid)
        self.assertAlmostEqual(total_sum, 1.0, places=3)
        self.assertTrue(all(v >= 0.0 for v in probs_map.values()))

    def test_multi_objective_ranking(self):
        """Verifies multi-objective strategy sorting."""
        engine = MonteCarloRaceEngine(iterations=2000, seed=42)

        # Max Podium Sort
        rankings_podium = engine.rank_strategies(self.driver_target, self.opponents, self.race_state, objective=ObjectiveType.MAX_PODIUM)
        self.assertTrue(rankings_podium[0].podium_probability >= rankings_podium[-1].podium_probability)

        # Min Position Sort
        rankings_pos = engine.rank_strategies(self.driver_target, self.opponents, self.race_state, objective=ObjectiveType.MIN_POSITION)
        self.assertTrue(rankings_pos[0].expected_position <= rankings_pos[-1].expected_position)

    def test_sensitivity_analysis_engine(self):
        """Verifies OAT sensitivity perturbation factors."""
        strat = StrategyPlan("1-Stop (Hard)", [StintPlan("MEDIUM", 15, 25), StintPlan("HARD", 25, 50)], [25], ["MEDIUM", "HARD"], 1)
        sens_res = SensitivityAnalysisEngine.evaluate_sensitivity(strat, self.driver_target, self.opponents, self.race_state, iterations=1000)

        self.assertIn("baseline_podium_pct", sens_res)
        # Comprehensive OAT sensitivity factors now include Tyre, Safety Car, Pit Loss, Fuel, and Track Evolution
        self.assertEqual(len(sens_res["sensitivity_factors"]), 5)

    def test_scenario_preset_modifications(self):
        """Verifies scenario presets modify race_state parameters."""
        scen_state = ScenarioEngine.apply_scenario(self.race_state, ScenarioPreset.HIGH_DEG)
        self.assertEqual(scen_state.weather.track_temp_c, 48.0)

        scen_rain = ScenarioEngine.apply_scenario(self.race_state, ScenarioPreset.HEAVY_RAIN)
        self.assertTrue(scen_rain.weather.rainfall)

    def test_performance_benchmark(self):
        """Measures runtime throughput for 10,000, 50,000, and 100,000 simulation runs."""
        strat = StrategyPlan("Benchmark Strategy", [StintPlan("MEDIUM", 15, 30), StintPlan("HARD", 30, 50)], [30], ["MEDIUM", "HARD"], 1)

        print("\n=== MONTE CARLO RACE ENGINE PERFORMANCE BENCHMARK ===")
        for count in [10000, 50000, 100000]:
            engine = MonteCarloRaceEngine(iterations=count, seed=42)
            t0 = time.perf_counter()
            out = engine.simulate_strategy_vectorized(strat, self.driver_target, self.opponents, self.race_state)
            t_ms = (time.perf_counter() - t0) * 1000.0

            print(f"- {count:,} Simulations Latency: {t_ms:.2f} ms | Expected Pos: P{out.expected_position:.2f}")
            self.assertTrue(t_ms < 5000.0)  # Must execute under 5s even at 100k scale


if __name__ == '__main__':
    unittest.main()
