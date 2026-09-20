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
        """Verifies Undercut & Overcut success probabilities and gains."""
        uo = api_service.analyze_undercut_overcut("VER", "HAM", gap_s=2.84)

        self.assertTrue(0.0 <= uo["undercut_success_probability_pct"] <= 100.0)
        self.assertTrue(0.0 <= uo["overcut_success_probability_pct"] <= 100.0)
        self.assertEqual(uo["recommended_tactic"], "EXECUTE_UNDERCUT")

    def test_api_service_strategy_routes(self):
        """Verifies API routes for canonical strategy state, undercut/overcut, and authoritative evaluation."""
        state = api_service.get_canonical_strategy_state("S-2024-SPAIN", 22, "VER")
        uo = api_service.analyze_undercut_overcut("VER", "HAM", 2.84)
        eval_res = api_service.evaluate_authoritative_strategy("S-2024-SPAIN", 22, "VER")

        self.assertEqual(state["driver_id"], "VER")
        self.assertEqual(uo["recommended_tactic"], "EXECUTE_UNDERCUT")
        
        # The API route correctly uses the production DecisionEngine.
        # Since FastF1 telemetry is available, it should generate a real strategy.
        self.assertIn("win_probability_pct", eval_res)
        self.assertNotEqual(eval_res["recommended_action"], "UNAVAILABLE")
        self.assertGreaterEqual(eval_res["win_probability_pct"], 0.0)


if __name__ == '__main__':
    unittest.main()
