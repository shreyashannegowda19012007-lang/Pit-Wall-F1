"""
Automated Unit, Integration & Bayesian Conjugate Test Suite for Unified Tyre Intelligence Subsystem.
Verifies CanonicalTyreState calculation, 3-Layer Thermal Model physics, Bayesian Conjugate Updating math,
compound crossover forecasting, optimal pit window forecasting, and API routes.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from unified_tyre_intelligence import UnifiedTyreIntelligenceEngine, CanonicalTyreState, CompoundCrossoverForecast, PitWindowForecast
from telemetry_api import api_service


class TestUnifiedTyreIntelligenceEngine(unittest.TestCase):

    def test_bayesian_conjugate_update_math(self):
        """Verifies Bayesian conjugate update equation calculates posterior mean & std correctly."""
        bayes = UnifiedTyreIntelligenceEngine.calculate_bayesian_posterior(
            prior_mean=0.075,
            prior_std=0.020,
            observed_mean=0.091,
            observed_std=0.015,
            n_obs=10
        )

        self.assertIn("posterior_mean", bayes)
        self.assertIn("posterior_std", bayes)

        # Posterior mean moves toward observations (between 0.075 and 0.091)
        self.assertTrue(0.075 < bayes["posterior_mean"] < 0.091)
        # Posterior std is tighter than prior std
        self.assertTrue(bayes["posterior_std"] < bayes["prior_std"])

    def test_canonical_tyre_state_generation(self):
        """Verifies CanonicalTyreState incorporates 3-layer thermal model and cliff probability."""
        state = UnifiedTyreIntelligenceEngine.get_canonical_tyre_state("VER", "MEDIUM", stint_lap=15)

        self.assertEqual(state.driver_id, "VER")
        self.assertEqual(state.compound, "MEDIUM")
        self.assertEqual(state.stint_lap, 15)

        # 3-Layer Thermal: Surface > Bulk > Core
        self.assertTrue(state.surface_temp_c > state.bulk_temp_c > state.core_temp_c)
        self.assertEqual(state.source_classification, "MODELLED")

    def test_compound_crossover_and_pit_window_forecasts(self):
        """Verifies compound crossover and optimal pit window forecasts."""
        cross = UnifiedTyreIntelligenceEngine.forecast_compound_crossover("MEDIUM", "HARD")
        pit_win = UnifiedTyreIntelligenceEngine.forecast_optimal_pit_window(15)

        self.assertEqual(cross.compound_a, "MEDIUM")
        self.assertEqual(cross.crossover_lap, 10)
        self.assertEqual(pit_win.optimal_pit_lap, 16)

    def test_api_service_unified_tyre_routes(self):
        """Verifies API routes for canonical tyre state, crossover, and pit window."""
        state = api_service.get_canonical_tyre_state("VER", "MEDIUM", 15)
        cross = api_service.get_compound_crossover_forecast("MEDIUM", "HARD")
        pit_win = api_service.get_optimal_pit_window_forecast(15)

        self.assertEqual(state["driver_id"], "VER")
        self.assertEqual(cross["crossover_lap"], 10)
        self.assertEqual(pit_win["optimal_pit_lap"], 16)


if __name__ == '__main__':
    unittest.main()
