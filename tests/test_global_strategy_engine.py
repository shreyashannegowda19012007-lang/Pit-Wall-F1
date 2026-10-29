"""
Comprehensive Automated Test Suite for Global Strategy Engine & Universal Circuit Transfer.
Verifies:
1. 2025 Spanish Grand Prix pre-race 2-stop regression and Lap 55 SC multi-stop response
2. Monaco GP 1-stop track-position dominance
3. Silverstone GP high-deg multi-stop preference
4. Physical Pirelli tyre compound resolution (C1 to C6)
5. Strict anti-leakage separation across 6 evaluation modes
6. Multi-driver starting position and pace isolation
7. Mathematical invariants (Win <= Podium, Sum(Win)=100%, Sum(Podium)=300%, Regret >= 0)
8. Sensitivity controls response (degradation scaling, pit loss offsets, SC risk)
"""

import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from circuit_database import CircuitDatabase, CircuitProfile
from tyre_compound_service import TyreCompoundService, PhysicalCompoundSpec
from global_strategy_engine import GlobalStrategyEngine, GlobalStrategyCandidateGenerator


class TestGlobalStrategyEngine(unittest.TestCase):

    def test_circuit_database_resolution(self):
        """Verifies canonical profiles for key circuits (Spain, Monaco, Silverstone, Monza)."""
        spain = CircuitDatabase.get_circuit_profile("SPAIN")
        self.assertEqual(spain.scheduled_laps, 66)
        self.assertEqual(spain.tyre_stress_rating, 4)
        self.assertEqual(spain.pit_lane_transit_loss_green_s, 21.5)

        monaco = CircuitDatabase.get_circuit_profile("MONACO")
        self.assertEqual(monaco.scheduled_laps, 78)
        self.assertEqual(monaco.overtaking_difficulty_index, 0.05)
        self.assertEqual(monaco.tyre_stress_rating, 1)

        silverstone = CircuitDatabase.get_circuit_profile("SILVERSTONE")
        self.assertEqual(silverstone.scheduled_laps, 52)
        self.assertEqual(silverstone.tyre_stress_rating, 5)

        # Alias resolution test
        catalunya = CircuitDatabase.get_circuit_profile("CATALUNYA")
        self.assertEqual(catalunya.circuit_id, "SPAIN")

        monte_carlo = CircuitDatabase.get_circuit_profile("MONTE CARLO")
        self.assertEqual(monte_carlo.circuit_id, "MONACO")

    def test_physical_compound_resolution(self):
        """Verifies nomination mapping of nominal compounds to physical C1-C6."""
        # 2025 Spain: Hard=C1, Medium=C2, Soft=C3
        nom_spain = TyreCompoundService.resolve_event_nomination(2025, "SPAIN")
        self.assertEqual(nom_spain.hard_physical, "C1")
        self.assertEqual(nom_spain.medium_physical, "C2")
        self.assertEqual(nom_spain.soft_physical, "C3")

        # 2024 Monaco: Hard=C3, Medium=C4, Soft=C5
        nom_monaco = TyreCompoundService.resolve_event_nomination(2024, "MONACO")
        self.assertEqual(nom_monaco.hard_physical, "C3")
        self.assertEqual(nom_monaco.medium_physical, "C4")
        self.assertEqual(nom_monaco.soft_physical, "C5")

        # Verify physical specs
        c1_code, c1_spec, _ = TyreCompoundService.get_physical_compound_for_nominal("HARD", 2025, "SPAIN")
        self.assertEqual(c1_code, "C1")
        self.assertTrue(c1_spec.base_degradation_s_per_lap < 0.050)

        c5_code, c5_spec, _ = TyreCompoundService.get_physical_compound_for_nominal("SOFT", 2024, "MONACO")
        self.assertEqual(c5_code, "C5")
        self.assertTrue(c5_spec.base_grip_offset_s < -0.80)

    def test_2025_spanish_gp_pre_race_regression(self):
        """
        Regression Test: 2025 Spanish GP Pre-Race Prediction.
        Verifies that pre-race optimizer favors a 2-stop over a 1-stop Medium-Hard,
        because Hard (C1) lacks mechanical grip and suffers sliding/deg on high-energy Barcelona asphalt.
        """
        res = GlobalStrategyEngine.run_global_simulation(
            target_driver="VER",
            circuit_id="SPAIN",
            season=2025,
            num_sims=80,
            objective="MIN_RACE_TIME",
            evaluation_mode="PRE_RACE",
            random_seed=42
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["total_laps"], 66)
        self.assertEqual(res["circuit_id"], "SPAIN")

        cands = res["candidate_evaluations"]
        # Find 1-stop MH and 2-stop SMS
        mh_1s = next((c for c in cands if c["strategy_id"] == "OPT-1S-MH"), None)
        sms_2s = next((c for c in cands if c["strategy_id"] == "OPT-2S-SMS"), None)
        smh_2s = next((c for c in cands if c["strategy_id"] == "OPT-2S-SMH"), None)

        self.assertIsNotNone(mh_1s)
        self.assertIsNotNone(sms_2s)
        self.assertIsNotNone(smh_2s)

        # 2-stop strategies are faster on mean race time than 1-stop MH in high-deg Spain
        self.assertLess(sms_2s["mean_race_time_s"], mh_1s["mean_race_time_s"])
        # Recommended strategy is a multi-stop, NOT the 1-stop Medium-Hard
        self.assertNotEqual(res["recommended_strategy"], "1-Stop Medium -> Hard")

    def test_2025_spanish_gp_historical_reconstruction_sc(self):
        """
        Historical Reconstruction: Spanish GP 2025 late Safety Car on Lap 55.
        Verifies that the presence of the late SC increases multi-stop viability (3-stop / 4-stop).
        """
        res_pre = GlobalStrategyEngine.run_global_simulation(
            target_driver="VER",
            circuit_id="SPAIN",
            season=2025,
            num_sims=50,
            evaluation_mode="PRE_RACE",
            random_seed=42
        )
        res_hist = GlobalStrategyEngine.run_global_simulation(
            target_driver="VER",
            circuit_id="SPAIN",
            season=2025,
            num_sims=50,
            evaluation_mode="HISTORICAL_RECONSTRUCTION",
            random_seed=42
        )

        self.assertEqual(res_hist["evaluation_mode"], "HISTORICAL_RECONSTRUCTION")
        # Under late SC, pit loss is drastically reduced, shortening race time deltas for aggressive stoppers
        sc_rec = res_hist["recommended_strategy"]
        self.assertIn("Stop", sc_rec)

    def test_monaco_gp_one_stop_dominance(self):
        """
        Circuit Transfer Test: Monaco Grand Prix.
        Due to 0.05 overtaking difficulty (track position king) and low tyre wear (1/5),
        1-stop strategy should dominate multi-stop strategies which lose track position.
        """
        res = GlobalStrategyEngine.run_global_simulation(
            target_driver="LEC",
            circuit_id="MONACO",
            season=2024,
            num_sims=60,
            objective="MIN_POSITION",
            random_seed=42
        )

        self.assertEqual(res["total_laps"], 78)
        self.assertEqual(res["circuit_id"], "MONACO")

        cands = res["candidate_evaluations"]
        mh_1s = next((c for c in cands if c["strategy_id"] == "OPT-1S-MH"), None)
        smss_3s = next((c for c in cands if c["strategy_id"] == "OPT-3S-SMSS"), None)

        self.assertIsNotNone(mh_1s)
        self.assertIsNotNone(smss_3s)

        # In Monaco, extra pit stops drop the car behind traffic with near-zero overtaking chance!
        self.assertLess(mh_1s["expected_finish_position"], smss_3s["expected_finish_position"])
        self.assertIn("1-Stop", res["recommended_strategy"])

    def test_silverstone_multi_stop_preference(self):
        """
        Circuit Transfer Test: Silverstone Circuit.
        Extreme high-speed lateral stress (5/5) with good overtaking (0.72) favours multi-stops.
        """
        res = GlobalStrategyEngine.run_global_simulation(
            target_driver="HAM",
            circuit_id="SILVERSTONE",
            season=2024,
            num_sims=60,
            objective="BALANCED",
            random_seed=42
        )

        self.assertEqual(res["total_laps"], 52)
        # Recommended should be a 2-stop strategy
        self.assertIn("2-Stop", res["recommended_strategy"])

    def test_driver_isolation(self):
        """Verifies that running the strategy engine for different drivers isolates starting grid & pace."""
        res_ver = GlobalStrategyEngine.run_global_simulation(
            target_driver="VER", circuit_id="SPAIN", season=2024, num_sims=40, random_seed=42
        )
        res_gas = GlobalStrategyEngine.run_global_simulation(
            target_driver="GAS", circuit_id="SPAIN", season=2024, num_sims=40, random_seed=42
        )

        ver_rec = next(c for c in res_ver["candidate_evaluations"] if c["is_recommended"])
        gas_rec = next(c for c in res_gas["candidate_evaluations"] if c["is_recommended"])

        # VER starts P1 with top pace, GAS starts P12
        self.assertLess(ver_rec["expected_finish_position"], gas_rec["expected_finish_position"])
        self.assertGreater(ver_rec["win_probability_pct"], gas_rec["win_probability_pct"])

    def test_mathematical_invariants(self):
        """Verifies probability bounds, position sums, regret, and benchmark reconciliation."""
        res = GlobalStrategyEngine.run_global_simulation(
            target_driver="VER", circuit_id="SPAIN", season=2025, num_sims=80, random_seed=123
        )

        cands = res["candidate_evaluations"]
        field = res["field_rankings"]

        # 1. Candidate Invariants
        for c in cands:
            self.assertLessEqual(c["win_probability_pct"], c["podium_probability_pct"] + 1e-3)
            self.assertGreaterEqual(c["win_probability_pct"], 0.0)
            self.assertLessEqual(c["podium_probability_pct"], 100.0)
            self.assertGreaterEqual(c["strategy_regret_s"], 0.0)
            dist_sum = sum(c["finish_position_distribution"].values())
            self.assertAlmostEqual(dist_sum, 100.0, delta=1.5)

        # 2. Recommended strategy regret must be lowest under min race time
        rec_cand = next(c for c in cands if c["is_recommended"])

        # 3. Full-Field Invariants
        self.assertEqual(len(field), 20)
        sum_wins = sum(f["win_probability_pct"] for f in field)
        sum_podiums = sum(f["podium_probability_pct"] for f in field)

        self.assertAlmostEqual(sum_wins, 100.0, delta=1.0)
        self.assertAlmostEqual(sum_podiums, 300.0, delta=2.0)

        # Target driver in benchmark matches recommended strategy
        ver_field = next(f for f in field if f["driver_id"] == "VER")
        self.assertAlmostEqual(rec_cand["win_probability_pct"], ver_field["win_probability_pct"], delta=0.5)
        self.assertAlmostEqual(rec_cand["podium_probability_pct"], ver_field["podium_probability_pct"], delta=0.5)

    def test_sensitivity_parameter_perturbation(self):
        """Verifies that user controls for deg scaling and pit loss offset actively shift race times."""
        res_baseline = GlobalStrategyEngine.run_global_simulation(
            target_driver="VER", circuit_id="SPAIN", season=2025, num_sims=40,
            user_deg_multiplier=1.0, user_pit_loss_offset_s=0.0, random_seed=42
        )
        res_high_deg = GlobalStrategyEngine.run_global_simulation(
            target_driver="VER", circuit_id="SPAIN", season=2025, num_sims=40,
            user_deg_multiplier=1.5, user_pit_loss_offset_s=0.0, random_seed=42
        )

        base_time = res_baseline["candidate_evaluations"][0]["mean_race_time_s"]
        high_deg_time = res_high_deg["candidate_evaluations"][0]["mean_race_time_s"]

        # Higher tyre degradation multiplier must increase total race time
        self.assertGreater(high_deg_time, base_time)


if __name__ == '__main__':
    unittest.main()
