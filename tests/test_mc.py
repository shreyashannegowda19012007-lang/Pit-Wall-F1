"""
Monte Carlo Race Simulator Integration Test.
Tests the core MC simulation pipeline without network calls or Streamlit UI rendering.
All data is constructed from race state objects — no live FastF1 fetches at import time.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath('src'))


class TestMonteCarloPipeline(unittest.TestCase):

    def test_mc_engine_imports_without_network(self):
        """Verifies Monte Carlo engine imports cleanly without network calls."""
        from monte_carlo_engine import MonteCarloRaceEngine
        self.assertTrue(callable(MonteCarloRaceEngine))

    def test_mc_engine_basic_simulation(self):
        """Tests basic MC simulation using synthetic race state — no FastF1 required."""
        from monte_carlo_engine import MonteCarloRaceEngine
        from race_state import (CompleteRaceState, DriverState, TyreState, FuelState,
                                 WeatherState, TrackState, SafetyCarState)
        from strategy_model import StrategyPlan, StintPlan

        # Build minimal synthetic race state
        tyre = TyreState(compound='MEDIUM', age_laps=8, remaining_grip_pct=85.0, thermal_deg_rate=0.07)
        fuel = FuelState(fuel_remaining_kg=55.0)
        driver = DriverState(driver_id='VER', position=2, current_gap_to_leader_s=2.5,
                             base_pace_s=82.0, tyre_state=tyre, fuel_state=fuel)
        opp_tyre = TyreState(compound='HARD', age_laps=4, remaining_grip_pct=92.0, thermal_deg_rate=0.07)
        opp = DriverState(driver_id='HAM', position=1, current_gap_to_leader_s=0.0,
                          base_pace_s=82.1, tyre_state=opp_tyre, fuel_state=FuelState(60.0))

        weather = WeatherState(condition='DRY', track_temp_c=30.0)
        track = TrackState(track_name='Test', total_laps=57, pit_lane_loss_seconds=22.5)
        sc = SafetyCarState(condition='GREEN', sc_probability_per_lap=0.02)
        race_state = CompleteRaceState(current_lap=25, total_laps=57,
                                       drivers={'VER': driver, 'HAM': opp},
                                       weather=weather, track=track, safety_car=sc)

        strategy = StrategyPlan(
            strategy_name='1-Stop',
            stints=[StintPlan('MEDIUM', 25, 15), StintPlan('HARD', 40, 17)],
            pit_laps=[40],
            compounds=['MEDIUM', 'HARD'],
            stop_count=1
        )

        engine = MonteCarloRaceEngine(iterations=200, seed=42)
        result = engine.simulate_strategy_vectorized(strategy, driver, [opp], race_state)

        self.assertIsNotNone(result)
        self.assertGreaterEqual(result.expected_position, 1.0)
        self.assertLessEqual(result.expected_position, 20.0)
        self.assertTrue(0.0 <= result.win_probability <= 1.0)
        self.assertTrue(0.0 <= result.podium_probability <= 1.0)
        self.assertGreater(result.expected_race_time_min, 0.0)

    def test_mc_rank_strategies(self):
        """Tests strategy ranking produces ordered results."""
        from monte_carlo_engine import MonteCarloRaceEngine
        from race_state import (CompleteRaceState, DriverState, TyreState, FuelState,
                                 WeatherState, TrackState, SafetyCarState)
        from strategy_model import ObjectiveType

        tyre = TyreState(compound='MEDIUM', age_laps=10, remaining_grip_pct=80.0, thermal_deg_rate=0.07)
        fuel = FuelState(fuel_remaining_kg=50.0)
        driver = DriverState('VER', 3, 5.0, 82.5, tyre, fuel)
        opponents = [
            DriverState('HAM', 1, 0.0, 82.0,
                        TyreState('HARD', 5, 90.0, 0.07), FuelState(55.0)),
            DriverState('LEC', 2, 2.5, 82.2,
                        TyreState('MEDIUM', 8, 88.0, 0.07), FuelState(52.0)),
        ]

        weather = WeatherState()
        track = TrackState()
        sc = SafetyCarState()
        race_state = CompleteRaceState(28, 57,
                                       {d.driver_id: d for d in [driver] + opponents},
                                       weather, track, sc)

        engine = MonteCarloRaceEngine(iterations=100, seed=42)
        results = engine.rank_strategies(driver, opponents, race_state, objective=ObjectiveType.MIN_POSITION)

        self.assertGreater(len(results), 0)
        # Results should be sorted by expected_position ascending
        positions = [r.expected_position for r in results]
        self.assertEqual(positions, sorted(positions))


if __name__ == '__main__':
    unittest.main()
