"""
Bayesian Race State & Snapshot Persistence Engine.
Stores Bayesian parameter posteriors and persists reproduceable lap-by-lap state snapshots.
Allows engineers to inspect model beliefs at any lap (e.g., "What did the model believe on Lap 15?").
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import datetime

from bayesian_updating import BayesianParameter, ConjugateBayesianEstimator
import pandas as pd


@dataclass
class BayesianRaceState:
    """
    State container for all active Bayesian posteriors and persistent lap snapshots.
    """
    race_lap: int
    parameters: Dict[str, BayesianParameter] = field(default_factory=dict)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    posterior_version: str = "v2.4.0"
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    state_snapshots: Dict[int, Dict[str, Any]] = field(default_factory=dict)

    def record_snapshot(self, lap_num: int):
        """Records state snapshot at specified lap."""
        self.race_lap = lap_num
        self.state_snapshots[lap_num] = {
            "race_lap": lap_num,
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "posterior_version": self.posterior_version,
            "parameters": {k: v.to_dict() for k, v in self.parameters.items()},
            "observation_count": len(self.observations)
        }

    def get_snapshot(self, lap_num: int) -> Optional[Dict[str, Any]]:
        """Retrieves exact Bayesian state snapshot recorded at specified lap."""
        return self.state_snapshots.get(lap_num)

    def update_from_telemetry(self, laps_df: pd.DataFrame, target_driver: str, current_lap: int):
        """
        Executes sequential Bayesian updates across parameters using telemetry up to current_lap.
        """
        if laps_df.empty:
            return

        # Slice observed telemetry UP TO current_lap to prevent data leakage
        observed_df = laps_df[laps_df['LapNumber'] <= current_lap].copy()

        # 1. Update Tyre Degradation
        tyre_param = ConjugateBayesianEstimator.update_tyre_degradation(
            compound="MEDIUM",
            observed_laps_df=observed_df,
            driver_id=target_driver,
            prior_deg_mean=0.07,
            prior_deg_std=0.02
        )
        self.parameters["tyre_degradation"] = tyre_param

        # 2. Update Driver Pace Baseline
        pace_param = ConjugateBayesianEstimator.update_driver_pace(
            driver_id=target_driver,
            observed_laps_df=observed_df,
            prior_pace_mean=90.0,
            prior_pace_std=0.5
        )
        self.parameters["driver_pace"] = pace_param

        # Record snapshot
        self.record_snapshot(current_lap)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "race_lap": self.race_lap,
            "posterior_version": self.posterior_version,
            "updated_at": self.updated_at,
            "parameters": {k: v.to_dict() for k, v in self.parameters.items()},
            "available_snapshots": list(self.state_snapshots.keys())
        }

