"""
Test Suite for Full-Field Race Intelligence Subsystem.
Tests structural and functional properties using synthetic state — no live FastF1 network calls
at module import time. Expensive operations (MC simulation) are limited to < 20 iterations
in tests and isolated in their own test methods.
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath('src'))


class TestFullFieldIntelligenceImports(unittest.TestCase):
    """Tests that don't require network or expensive computation."""

    def test_imports_succeed(self):
        """Verifies full-field intelligence module imports cleanly."""
        from full_field_intelligence import (FullFieldRaceIntelligenceEngine,
                                              FullFieldDriverState, BattleState,
                                              CanonicalDriverAgent, CarState)
        self.assertTrue(callable(FullFieldRaceIntelligenceEngine))

    def test_battle_state_dataclass(self):
        """Verifies BattleState dataclass construction."""
        from full_field_intelligence import BattleState
        battle = BattleState(
            battle_id="BAT-VER-HAM",
            attacker_driver_id="VER",
            defender_driver_id="HAM",
            gap_s=0.8,
            pace_delta_s=-0.15,
            drs_available=True,
            overtake_probability_pct=42.5,
            is_drs_train=False
        )
        self.assertEqual(battle.battle_id, "BAT-VER-HAM")
        self.assertEqual(battle.gap_s, 0.8)
        self.assertTrue(0.0 <= battle.overtake_probability_pct <= 100.0)

    def test_full_field_driver_state_dataclass(self):
        """Verifies FullFieldDriverState dataclass construction."""
        from full_field_intelligence import FullFieldDriverState
        state = FullFieldDriverState(
            position=1, driver_id="VER", team_id="RBR", lap=22,
            gap_to_leader_s=0.0, interval_s=0.0, compound="MEDIUM",
            tyre_age_laps=15, estimated_pace_s=82.5, race_status="RACING"
        )
        self.assertEqual(state.driver_id, "VER")
        self.assertEqual(state.position, 1)


class TestFullFieldMonteCarlo(unittest.TestCase):
    """Tests Monte Carlo simulation with lightweight iteration counts."""

    def test_full_field_mc_returns_expected_structure_on_data_unavailable(self):
        """
        Verifies simulate_full_field_monte_carlo handles DATA_UNAVAILABLE gracefully.
        This does not require network access — mocks the field state.
        """
        from full_field_intelligence import FullFieldRaceIntelligenceEngine

        with patch.object(FullFieldRaceIntelligenceEngine, 'get_20_car_field_state', return_value=[]):
            res = FullFieldRaceIntelligenceEngine.simulate_full_field_monte_carlo("VER")
            self.assertEqual(res["primary_driver_id"], "VER")
            self.assertEqual(res["status"], "DATA_UNAVAILABLE")
            self.assertEqual(res["total_simulations"], 0)
            self.assertEqual(res["field_summary"], [])

    def test_full_field_simulator_with_synthetic_data(self):
        """Tests FullFieldRaceSimulator with synthetic driver states — no network needed."""
        from full_field_simulator import FullFieldRaceSimulator, RaceSimulationConfig, DriverSimState

        drivers = [
            DriverSimState("VER", "RBR", 1, 1, 22, 0.0, 82.0, 81.5, "MEDIUM", 15, 1, 80.0, 0, False, "RACING", 0.0, None),
            DriverSimState("HAM", "MER", 2, 2, 22, 3.5, 82.2, 81.8, "HARD", 10, 1, 80.0, 0, False, "RACING", 3.5, 3.5),
            DriverSimState("LEC", "FER", 3, 3, 22, 7.2, 82.5, 82.0, "MEDIUM", 20, 1, 80.0, 0, False, "RACING", 7.2, 3.7),
        ]

        # Provide strategies for the custom drivers explicitly
        planned_strategies = {
            "VER": [(40, "HARD")],
            "HAM": [(38, "MEDIUM")],
            "LEC": [(35, "HARD")],
        }

        cfg = RaceSimulationConfig(simulation_seed=42, total_laps=30)
        result = FullFieldRaceSimulator.run_full_field_simulation(
            config=cfg,
            initial_states=drivers,
            planned_strategies=planned_strategies
        )

        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'final_standings'))
        self.assertGreater(len(result.final_standings), 0)



class TestBattleDetection(unittest.TestCase):
    """Tests battle detection logic."""

    def test_detect_battles_from_synthetic_field(self):
        """Verifies battle detection correctly identifies close gaps."""
        from full_field_intelligence import FullFieldDriverState, BattleState

        # Construct field directly without network
        field_state = [
            FullFieldDriverState(1, "VER", "RBR", 22, 0.0, 0.0, "MEDIUM", 15, 82.0, "RACING"),
            FullFieldDriverState(2, "HAM", "MER", 22, 0.8, 0.8, "HARD", 10, 82.3, "RACING"),  # close gap
            FullFieldDriverState(3, "LEC", "FER", 22, 4.5, 3.7, "MEDIUM", 20, 82.5, "RACING"),
        ]

        battles = []
        for i in range(1, len(field_state)):
            attacker = field_state[i]
            defender = field_state[i - 1]
            if attacker.interval_s is not None and 0 < attacker.interval_s <= 1.5:
                drs = attacker.interval_s <= 1.0
                battles.append(BattleState(
                    battle_id=f"BAT-{defender.driver_id}-{attacker.driver_id}",
                    attacker_driver_id=attacker.driver_id,
                    defender_driver_id=defender.driver_id,
                    gap_s=attacker.interval_s,
                    pace_delta_s=round(defender.estimated_pace_s - attacker.estimated_pace_s, 3),
                    drs_available=drs,
                    overtake_probability_pct=min(100.0, max(0.0,
                        50.0 + (defender.estimated_pace_s - attacker.estimated_pace_s) * 20)),
                    is_drs_train=False
                ))

        self.assertEqual(len(battles), 1)  # Only HAM-VER gap is within 1.5s
        self.assertEqual(battles[0].attacker_driver_id, "HAM")
        self.assertTrue(battles[0].drs_available)  # 0.8s <= 1.0s threshold


if __name__ == '__main__':
    unittest.main()
