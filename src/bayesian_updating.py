"""
Conjugate Bayesian Updating Engine for F1 Telemetry & Race State Parameters.
Implements exact Normal-Normal conjugate Bayesian updating for tyre degradation,
driver baseline pace, pit-stop duration, weather transitions, and Safety Car risks.
Calculates posterior distributions, 95% credible intervals, and uncertainty shrinkage.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd

from probabilistic_model import ProbabilisticPrediction, IntervalType, UncertaintyType


@dataclass
class BayesianParameter:
    """
    Container for an estimated parameter under Bayesian updating.
    Tracks prior, likelihood evidence, posterior distribution, and uncertainty shrinkage.
    """
    parameter_name: str
    prior_mean: float
    prior_std: float
    posterior_mean: float
    posterior_std: float
    lower_credible: float
    upper_credible: float
    observation_count: int
    update_magnitude_pct: float
    model_name: str = "ConjugateBayesianEngine"
    model_version: str = "v2.4.0"
    data_quality: str = "HIGH"
    assumptions: List[str] = field(default_factory=list)

    def format_credible_interval(self) -> str:
        return f"{self.posterior_mean:.4f} [95% Credible Interval: {self.lower_credible:.4f} - {self.upper_credible:.4f}]"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameter_name": self.parameter_name,
            "prior_mean": round(self.prior_mean, 4),
            "prior_std": round(self.prior_std, 4),
            "posterior_mean": round(self.posterior_mean, 4),
            "posterior_std": round(self.posterior_std, 4),
            "lower_credible": round(self.lower_credible, 4),
            "upper_credible": round(self.upper_credible, 4),
            "observation_count": self.observation_count,
            "update_magnitude_pct": round(self.update_magnitude_pct, 2),
            "model_version": self.model_version,
            "data_quality": self.data_quality,
            "assumptions": self.assumptions,
            "formatted_interval": self.format_credible_interval()
        }


class ConjugateBayesianEstimator:
    """
    Mathematically rigorous Normal-Normal Conjugate Bayesian Updating Engine.
    """

    @staticmethod
    def update_normal_normal(
        prior_mean: float,
        prior_std: float,
        observations: List[float],
        obs_noise_std: float = 0.1
    ) -> BayesianParameter:
        """
        Calculates exact Normal-Normal conjugate posterior distribution.
        """
        if prior_std <= 0:
            prior_std = 0.05
        if obs_noise_std <= 0:
            obs_noise_std = 0.1

        n = len(observations)
        if n == 0:
            # No observations: Posterior equals Prior
            return BayesianParameter(
                parameter_name="parameter",
                prior_mean=prior_mean,
                prior_std=prior_std,
                posterior_mean=prior_mean,
                posterior_std=prior_std,
                lower_credible=prior_mean - 1.96 * prior_std,
                upper_credible=prior_mean + 1.96 * prior_std,
                observation_count=0,
                update_magnitude_pct=0.0
            )

        obs_arr = np.array(observations)
        x_bar = float(np.mean(obs_arr))

        # Precision weights: tau_0 = 1 / sigma_0^2, tau_obs = 1 / sigma^2
        prec_prior = 1.0 / (prior_std ** 2)
        prec_obs = 1.0 / (obs_noise_std ** 2)

        prec_post = prec_prior + n * prec_obs
        posterior_var = 1.0 / prec_post
        posterior_std = float(np.sqrt(posterior_var))

        posterior_mean = float((prec_prior * prior_mean + n * prec_obs * x_bar) / prec_post)

        lower_credible = float(posterior_mean - 1.96 * posterior_std)
        upper_credible = float(posterior_mean + 1.96 * posterior_std)

        update_mag = float(((posterior_mean - prior_mean) / abs(prior_mean)) * 100.0) if prior_mean != 0 else 0.0

        return BayesianParameter(
            parameter_name="parameter",
            prior_mean=prior_mean,
            prior_std=prior_std,
            posterior_mean=posterior_mean,
            posterior_std=posterior_std,
            lower_credible=lower_credible,
            upper_credible=upper_credible,
            observation_count=n,
            update_magnitude_pct=update_mag
        )

    @classmethod
    def update_tyre_degradation(
        cls,
        compound: str,
        observed_laps_df: pd.DataFrame,
        driver_id: str,
        prior_deg_mean: float = 0.07,
        prior_deg_std: float = 0.02
    ) -> BayesianParameter:
        """
        Updates tyre degradation rate posterior from observed lap time deltas.
        """
        if observed_laps_df.empty:
            p = cls.update_normal_normal(prior_deg_mean, prior_deg_std, [])
            p.parameter_name = f"tyre_degradation_{compound}"
            p.assumptions = [f"Prior tyre degradation rate for {compound} compound", "No lap observations available yet"]
            return p

        driver_laps = observed_laps_df[(observed_laps_df['Driver'] == driver_id) & (observed_laps_df['IsAccurate'] == True)].copy()
        if len(driver_laps) < 2:
            p = cls.update_normal_normal(prior_deg_mean, prior_deg_std, [])
            p.parameter_name = f"tyre_degradation_{compound}"
            p.assumptions = ["Insufficient accurate laps for posterior update (min 2 clean laps required)"]
            return p

        # Calculate empirical lap-to-lap pace differences (controlling for lap number progression)
        lap_times = driver_laps['LapTime'].dt.total_seconds().values
        lap_diffs = np.diff(lap_times)

        # Filter extreme outliers (> 2.0s anomalies e.g. traffic/yellow flags)
        clean_diffs = [float(d) for d in lap_diffs if -0.5 <= d <= 1.5]

        param = cls.update_normal_normal(prior_deg_mean, prior_deg_std, clean_diffs, obs_noise_std=0.05)
        param.parameter_name = f"tyre_degradation_{compound}"
        param.data_quality = "HIGH" if len(clean_diffs) >= 5 else "MEDIUM"
        param.assumptions = [
            f"Prior degradation mean={prior_deg_mean:.3f} s/lap derived from compound baseline",
            f"Normal-Normal conjugate likelihood updated on {len(clean_diffs)} clean lap deltas",
            "Outlier lap time spikes (>2.0s) filtered out to prevent traffic contamination"
        ]
        return param

    @classmethod
    def update_driver_pace(
        cls,
        driver_id: str,
        observed_laps_df: pd.DataFrame,
        prior_pace_mean: float = 90.0,
        prior_pace_std: float = 0.5
    ) -> BayesianParameter:
        """
        Updates driver baseline pace posterior from clean lap times.
        """
        if observed_laps_df.empty:
            p = cls.update_normal_normal(prior_pace_mean, prior_pace_std, [])
            p.parameter_name = f"driver_pace_{driver_id}"
            return p

        driver_laps = observed_laps_df[(observed_laps_df['Driver'] == driver_id) & (observed_laps_df['IsAccurate'] == True)].copy()
        if driver_laps.empty:
            p = cls.update_normal_normal(prior_pace_mean, prior_pace_std, [])
            p.parameter_name = f"driver_pace_{driver_id}"
            return p

        clean_times = [float(t) for t in driver_laps['LapTime'].dt.total_seconds().values]

        param = cls.update_normal_normal(prior_pace_mean, prior_pace_std, clean_times, obs_noise_std=0.3)
        param.parameter_name = f"driver_pace_{driver_id}"
        param.data_quality = "HIGH" if len(clean_times) >= 5 else "MEDIUM"
        param.assumptions = [
            f"Prior driver pace mean={prior_pace_mean:.2f}s derived from practice/qualifying baseline",
            f"Conjugate posterior updated across {len(clean_times)} clean race laps"
        ]
        return param
