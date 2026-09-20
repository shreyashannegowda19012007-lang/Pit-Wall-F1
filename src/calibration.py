"""
Probability Calibration & Evaluation Engine for F1 Predictive Framework.
Calculates Brier Score, Log Loss, and Reliability Diagram data for probability calibration.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np


class ProbabilityCalibrationEngine:
    """
    Evaluates probability calibration and predictive accuracy metrics.
    """

    @staticmethod
    def calculate_brier_score(predictions: List[float], actuals: List[int]) -> float:
        """
        Computes Brier score: Mean Squared Error of probability predictions versus binary outcomes.
        Lower is better (0.0 = perfect calibration).
        """
        if not predictions or not actuals or len(predictions) != len(actuals):
            return 1.0

        p = np.clip(np.array(predictions), 0.0, 1.0)
        y = np.array(actuals)
        return float(np.mean((p - y) ** 2))

    @staticmethod
    def calculate_log_loss(predictions: List[float], actuals: List[int], eps: float = 1e-15) -> float:
        """
        Computes Logarithmic Loss (Cross-Entropy).
        """
        if not predictions or not actuals or len(predictions) != len(actuals):
            return 10.0

        p = np.clip(np.array(predictions), eps, 1.0 - eps)
        y = np.array(actuals)
        return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1.0 - p)))

    @staticmethod
    def generate_reliability_diagram(predictions: List[float], actuals: List[int], num_bins: int = 10) -> Dict[str, Any]:
        """
        Generates reliability diagram data bins comparing predicted probabilities against empirical observed frequencies.
        Computes Expected Calibration Error (ECE).
        """
        if not predictions or not actuals or len(predictions) != len(actuals):
            return {"bins": [], "expected_calibration_error": 1.0}

        p = np.clip(np.array(predictions), 0.0, 1.0)
        y = np.array(actuals)
        bin_edges = np.linspace(0.0, 1.0, num_bins + 1)

        bins_data = []
        ece = 0.0
        n_total = len(p)

        for i in range(num_bins):
            bin_lower = bin_edges[i]
            bin_upper = bin_edges[i + 1]

            mask = (p >= bin_lower) & (p < bin_upper) if i < num_bins - 1 else (p >= bin_lower) & (p <= bin_upper)
            bin_count = int(np.sum(mask))

            if bin_count > 0:
                mean_pred = float(np.mean(p[mask]))
                mean_actual = float(np.mean(y[mask]))
                diff = abs(mean_pred - mean_actual)
                ece += (bin_count / n_total) * diff
            else:
                mean_pred = float(0.5 * (bin_lower + bin_upper))
                mean_actual = 0.0
                diff = 0.0

            bins_data.append({
                "bin_index": i + 1,
                "bin_range": [round(float(bin_lower), 2), round(float(bin_upper), 2)],
                "count": bin_count,
                "mean_predicted": round(mean_pred, 3),
                "observed_frequency": round(mean_actual, 3),
                "calibration_error": round(diff, 3)
            })

        return {
            "num_bins": num_bins,
            "total_samples": n_total,
            "expected_calibration_error": round(float(ece), 4),
            "brier_score": round(ProbabilityCalibrationEngine.calculate_brier_score(predictions, actuals), 4),
            "log_loss": round(ProbabilityCalibrationEngine.calculate_log_loss(predictions, actuals), 4),
            "bins": bins_data
        }

