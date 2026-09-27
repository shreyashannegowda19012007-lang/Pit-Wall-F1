"""
Automated Unit, Integration & Probabilistic Decision Test Suite for Authoritative Strategy Subsystem.
Verifies API routes for canonical strategy state, undercut/overcut calculations, and authoritative decision evaluation.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from telemetry_api import api_service
from probabilistic_service import ProbabilisticService


class TestAuthoritativeStrategyEngine(unittest.TestCase):

    def test_undercut_overcut_tactical_analysis(self):
        """Verifies Undercut & Overcut success probabilities and gains across scenarios."""
        # Scenario 1: Primary driver is faster (Rival is slower, 83.0s), small gap (1.0s)
        # Should favor undercut because of pace advantage and proximity.
        uo_faster = api_service.analyze_undercut_overcut("VER", "HAM", gap_s=1.0, base_pace_s=82.0, rival_base_pace_s=83.0)
        self.assertTrue(0.0 <= uo_faster["undercut_success_probability_pct"] <= 100.0)
        self.assertEqual(uo_faster["recommended_tactic"], "EXECUTE_UNDERCUT")

        # Scenario 2: Primary driver is much slower (Rival is faster, 81.0s)
        # Undercut probability drops drastically. Should recommend STAY_ON_CURRENT_PACE.
        uo_slower = api_service.analyze_undercut_overcut("VER", "HAM", gap_s=2.84, base_pace_s=82.0, rival_base_pace_s=81.0)
        self.assertEqual(uo_slower["recommended_tactic"], "STAY_ON_CURRENT_PACE")

        # Scenario 3: Large gap (20.0s), equal pace
        # Too far to undercut effectively.
        uo_far = api_service.analyze_undercut_overcut("VER", "HAM", gap_s=20.0, base_pace_s=82.0, rival_base_pace_s=82.0)
        self.assertEqual(uo_far["recommended_tactic"], "STAY_ON_CURRENT_PACE")
    def test_api_service_strategy_routes(self):
        """Verifies API routes for canonical strategy state, undercut/overcut, and authoritative evaluation."""
        state = api_service.get_canonical_strategy_state("S-2024-SPAIN", 22, "VER")
        uo = api_service.analyze_undercut_overcut("VER", "HAM", 2.84)
        eval_res = api_service.evaluate_authoritative_strategy("S-2024-SPAIN", 22, "VER")

        self.assertEqual(state["driver_id"], "VER")
        # Default mock has rival 0.2s faster, so undercut fails
        self.assertEqual(uo["recommended_tactic"], "STAY_ON_CURRENT_PACE")

        # The API route correctly uses the production DecisionEngine.
        # Since FastF1 telemetry is available, it should generate a real strategy.
        self.assertIn("win_probability_pct", eval_res)
        self.assertNotEqual(eval_res["recommended_action"], "UNAVAILABLE")
        self.assertGreaterEqual(eval_res["win_probability_pct"], 0.0)


if __name__ == '__main__':
    unittest.main()
