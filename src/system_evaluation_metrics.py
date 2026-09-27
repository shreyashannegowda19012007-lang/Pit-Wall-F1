"""
System-Wide Formal Evaluation & Metrics Engine.
Computes mathematically rigorous metrics across telemetry, strategy, Bayesian updating,
probabilistic calibration, AI Engineer QA accuracy, latency, and bootstrap confidence intervals.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np


@dataclass
class MetricWithCI:
    name: str
    value: float
    ci_lower: float
    ci_upper: float
    unit: str = ""

    def format(self) -> str:
        if self.unit == "%":
            return f"{self.value:.1f}% [95% CI: {self.ci_lower:.1f}% - {self.ci_upper:.1f}%]"
        return f"{self.value:.4f} [95% CI: {self.ci_lower:.4f} - {self.ci_upper:.4f}] {self.unit}".strip()


class SystemEvaluationMetrics:
    """
    Core Metrics Calculation Library.
    """

    @staticmethod
    def calculate_mae(predictions: List[float], actuals: List[float]) -> float:
        if not predictions or len(predictions) != len(actuals):
            return 0.0
        return float(np.mean(np.abs(np.array(predictions) - np.array(actuals))))

    @staticmethod
    def calculate_rmse(predictions: List[float], actuals: List[float]) -> float:
        if not predictions or len(predictions) != len(actuals):
            return 0.0
        return float(np.sqrt(np.mean((np.array(predictions) - np.array(actuals)) ** 2)))

    @staticmethod
    def calculate_reconciliation_error(total_lap_losses: List[float], sum_attributed_losses: List[float]) -> Dict[str, float]:
        """Calculates residual error between total lap loss and sum of corner/sector segment losses."""
        if not total_lap_losses or len(total_lap_losses) != len(sum_attributed_losses):
            return {"mean_error": 0.0, "median_error": 0.0, "p95_error": 0.0, "max_error": 0.0}

        diffs = np.abs(np.array(total_lap_losses) - np.array(sum_attributed_losses))
        return {
            "mean_error": float(np.mean(diffs)),
            "median_error": float(np.median(diffs)),
            "p95_error": float(np.percentile(diffs, 95)),
            "max_error": float(np.max(diffs))
        }

    @staticmethod
    def calculate_brier_score(predictions: List[float], actuals: List[int]) -> float:
        if not predictions or len(predictions) != len(actuals):
            return 0.0
        return float(np.mean((np.array(predictions) - np.array(actuals)) ** 2))

    @staticmethod
    def calculate_bootstrap_ci(data: List[float], num_bootstraps: int = 1000, ci_pct: float = 95.0) -> Tuple[float, float, float]:
        """Calculates sample mean and paired bootstrap 95% confidence intervals."""
        if not data:
            return 0.0, 0.0, 0.0
        arr = np.array(data)
        mean_val = float(np.mean(arr))

        np.random.seed(42)
        boot_means = []
        n = len(arr)
        for _ in range(num_bootstraps):
            sample = np.random.choice(arr, size=n, replace=True)
            boot_means.append(np.mean(sample))

        alpha = (100.0 - ci_pct) / 2.0
        ci_lower = float(np.percentile(boot_means, alpha))
        ci_upper = float(np.percentile(boot_means, 100.0 - alpha))
        return mean_val, ci_lower, ci_upper

    @staticmethod
    def calculate_latency_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
        """Calculates latency summary statistics (Mean, Median, P95, P99)."""
        if not latencies_ms:
            return {"mean_ms": 0.0, "median_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}

        arr = np.array(latencies_ms)
        return {
            "mean_ms": round(float(np.mean(arr)), 2),
            "median_ms": round(float(np.median(arr)), 2),
            "p95_ms": round(float(np.percentile(arr, 95)), 2),
            "p99_ms": round(float(np.percentile(arr, 99)), 2)
        }
