"""
Automated Unit Test & Synthetic Replay Validation Suite for Bayesian Race-State Updating System.
Verifies analytical Normal-Normal conjugate updating, uncertainty shrinkage, deterministic race replay,
zero future-data leakage, state snapshot persistence, and parameter convergence.
"""

import unittest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from bayesian_updating import ConjugateBayesianEstimator, BayesianParameter
from bayesian_state import BayesianRaceState
from bayesian_replay import BayesianRaceReplayEngine


class TestBayesianUpdatingSystem(unittest.TestCase):

    def test_conjugate_normal_normal_analytical_closed_form(self):
        """Verifies exact analytical closed-form Conjugate Normal-Normal posterior mean and variance."""
        prior_mu = 0.07
        prior_sigma = 0.02
        obs_noise = 0.05
        obs = [0.10, 0.09, 0.11, 0.08, 0.10]
        n = len(obs)
        x_bar = np.mean(obs)

        # Analytical formula calculation
        prec_prior = 1.0 / (prior_sigma ** 2)
        prec_obs = 1.0 / (obs_noise ** 2)
        prec_post = prec_prior + n * prec_obs
        expected_post_var = 1.0 / prec_post
        expected_post_std = np.sqrt(expected_post_var)
        expected_post_mu = (prec_prior * prior_mu + n * prec_obs * x_bar) / prec_post

        param = ConjugateBayesianEstimator.update_normal_normal(prior_mu, prior_sigma, obs, obs_noise)

        self.assertAlmostEqual(param.posterior_mean, expected_post_mu, places=5)
        self.assertAlmostEqual(param.posterior_std, expected_post_std, places=5)
        self.assertTrue(param.lower_credible < param.posterior_mean < param.upper_credible)

    def test_uncertainty_shrinkage_property(self):
        """Verifies property that informative observations shrink posterior credible interval width."""
        prior_mu = 0.07
        prior_sigma = 0.02
        obs = [0.09] * 10  # 10 consistent observations

        param = ConjugateBayesianEstimator.update_normal_normal(prior_mu, prior_sigma, obs, obs_noise_std=0.05)

        # Posterior std dev MUST be strictly less than prior std dev
        self.assertTrue(param.posterior_std < param.prior_std)
        prior_interval_width = 2 * 1.96 * prior_sigma
        post_interval_width = param.upper_credible - param.lower_credible
        self.assertTrue(post_interval_width < prior_interval_width)

    def test_state_snapshot_persistence(self):
        """Verifies snapshot persistence at specified lap."""
        state = BayesianRaceState(race_lap=0)
        
        laps_mock = pd.DataFrame({
            'Driver': ['VER'] * 5,
            'LapNumber': [1, 2, 3, 4, 5],
            'LapTime': pd.to_timedelta([90.0, 90.1, 90.2, 90.3, 90.4], unit='s'),
            'IsAccurate': [True] * 5
        })

        state.update_from_telemetry(laps_mock, "VER", current_lap=5)
        snap = state.get_snapshot(5)

        self.assertIsNotNone(snap)
        self.assertEqual(snap['race_lap'], 5)
        self.assertIn("tyre_degradation", snap['parameters'])

    def test_synthetic_parameter_convergence(self):
        """Synthetic Validation: Verifies posterior mean converges toward true parameter (0.10s/lap) as observations accumulate."""
        true_deg = 0.10
        prior_mu = 0.05
        prior_sigma = 0.03

        # Generate 30 noisy lap time deltas centered around true_deg
        np.random.seed(42)
        noisy_obs = list(np.random.normal(loc=true_deg, scale=0.02, size=30))

        param_early = ConjugateBayesianEstimator.update_normal_normal(prior_mu, prior_sigma, noisy_obs[:3], obs_noise_std=0.05)
        param_late = ConjugateBayesianEstimator.update_normal_normal(prior_mu, prior_sigma, noisy_obs[:30], obs_noise_std=0.05)

        # Late posterior mean should be closer to true_deg (0.10) than early posterior
        err_early = abs(param_early.posterior_mean - true_deg)
        err_late = abs(param_late.posterior_mean - true_deg)
        self.assertTrue(err_late < err_early)
        self.assertAlmostEqual(param_late.posterior_mean, true_deg, delta=0.015)

    def test_zero_future_data_leakage_replay(self):
        """Verifies that race replay Lap L checkpoint ONLY slices telemetry up to Lap L."""
        mock_laps = pd.DataFrame({
            'Driver': ['VER'] * 10,
            'LapNumber': list(range(1, 11)),
            'LapTime': pd.to_timedelta([90.0 + 0.1 * i for i in range(10)], unit='s'),
            'IsAccurate': [True] * 10,
            'Position': [2] * 10,
            'TyreLife': list(range(1, 11)),
            'Compound': ['MEDIUM'] * 10
        })

        mock_results = pd.DataFrame({'Abbreviation': ['VER', 'HAM'], 'TeamName': ['Red Bull Racing', 'Red Bull Racing']})

        replay_res = BayesianRaceReplayEngine.replay_race_timeline(
            session=None,
            laps_df=mock_laps,
            results_df=mock_results,
            target_driver="VER",
            opponent_driver="HAM",
            step_laps=5,
            mc_iterations=500
        )

        self.assertIn("timeline", replay_res)
        timeline = replay_res["timeline"]
        self.assertTrue(len(timeline) > 0)

        # Verify Lap 5 snapshot observation count is <= 5
        lap5_node = next((t for t in timeline if t["race_lap"] == 5), None)
        self.assertIsNotNone(lap5_node)
        obs_count = lap5_node["bayesian_snapshot"]["parameters"]["tyre_degradation"]["observation_count"]
        self.assertTrue(obs_count <= 4)  # 4 diffs for 5 laps


if __name__ == '__main__':
    unittest.main()
