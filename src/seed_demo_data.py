import pandas as pd
import numpy as np
from typing import Tuple

class DemoDataSeeder:
    """Deterministic synthetic data generator for F1 telemetry and race states."""

    @classmethod
    def generate_synthetic_demo_dataset(cls, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generates identical synthetic telemetry laps and race results for a given seed.
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: laps_df, results_df
        """
        rng = np.random.RandomState(seed)

        drivers = ["VER", "HAM", "NOR", "LEC", "SAI", "RUS", "PER", "PIA"]
        laps = []

        for driver in drivers:
            base_time = rng.normal(82.0, 0.5)
            for lap in range(1, 58):
                lap_time = base_time + rng.normal(0, 0.2) + (lap * 0.05)
                laps.append({
                    "Driver": driver,
                    "LapNumber": lap,
                    "LapTime": pd.Timedelta(seconds=lap_time),
                    "Compound": rng.choice(["SOFT", "MEDIUM", "HARD"]),
                    "TyreLife": min(lap, 30),
                    "Time": pd.Timedelta(seconds=lap_time * lap)
                })

        laps_df = pd.DataFrame(laps)

        results = []
        for pos, driver in enumerate(drivers, start=1):
            results.append({
                "Abbreviation": driver,
                "Position": pos
            })

        results_df = pd.DataFrame(results)

        return laps_df, results_df
