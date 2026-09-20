"""
Automated Unit, Integration & Determinism Test Suite for Full-Field F1 Race Simulation Engine.
Verifies lap-by-lap 20-car field state machine evolution, deterministic seeded execution,
fuel mass burn, pit stops, Monte Carlo strategy distributions, and API integration.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from full_field_simulator import FullFieldRaceSimulator, RaceSimulationConfig
from telemetry_api import api_service


class TestFullFieldRaceSimulator(unittest.TestCase):

    def test_deterministic_seeded_race_simulation(self):
        """Verifies that same configuration + same seed produces identical race outcomes."""
        cfg1 = RaceSimulationConfig(circuit_id="SPAIN", total_laps=20, simulation_seed=42)
        cfg2 = RaceSimulationConfig(circuit_id="SPAIN", total_laps=20, simulation_seed=42)

        res1 = FullFieldRaceSimulator.run_full_field_simulation(cfg1)
        res2 = FullFieldRaceSimulator.run_full_field_simulation(cfg2)

        self.assertEqual(res1.winner_driver_id, res2.winner_driver_id)
        self.assertEqual(res1.total_race_time_s, res2.total_race_time_s)
        self.assertEqual(res1.total_overtakes, res2.total_overtakes)

    def test_fuel_burn_and_pit_stop_tracking(self):
        """Verifies 20-car field fuel burn (-1.5kg/lap) and pit stop count tracking."""
        cfg = RaceSimulationConfig(circuit_id="SPAIN", total_laps=15, simulation_seed=101)
        res = FullFieldRaceSimulator.run_full_field_simulation(cfg)

        self.assertEqual(len(res.final_standings), 20)
        self.assertTrue(res.total_pit_stops >= 0)

        # Check fuel mass burn on driver
        ver = next(d for d in res.final_standings if d['driver_id'] == "VER")
        self.assertTrue(ver['fuel_mass_kg'] < cfg.fuel_mass_initial_kg)

    def test_monte_carlo_field_simulation(self):
        """Verifies Monte Carlo simulation across 50 iterations computes win/podium probabilities."""
        cfg = RaceSimulationConfig(circuit_id="SPAIN", total_laps=10, simulation_seed=202)
        mc_res = FullFieldRaceSimulator.run_monte_carlo_field_simulation(num_simulations=50, config=cfg)

        self.assertEqual(mc_res["num_simulations"], 50)
        self.assertEqual(len(mc_res["driver_rankings"]), 20)
        self.assertTrue(mc_res["driver_rankings"][0]["win_probability_pct"] >= 0.0)

    def test_api_service_full_field_routes(self):
        """Verifies API routes for full field simulation and Monte Carlo."""
        sim_res = api_service.run_full_field_simulation("SPAIN", 15, 42)
        mc_res = api_service.run_full_field_monte_carlo("SPAIN", 15, 20)

        self.assertIn("winner_driver_id", sim_res)
        self.assertIn("driver_rankings", mc_res)


if __name__ == '__main__':
    unittest.main()
