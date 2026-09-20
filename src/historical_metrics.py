"""
Historical Evaluation Metrics & Regret Calculation Engine.
Calculates formal decision regret, Mean Absolute Error (MAE), Strategy Agreement %,
Brier Score, and Probability Calibration metrics for historical backtests.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np


class HistoricalReplayMetrics:
    """
    Computes mathematical evaluation metrics for historical race strategy backtests.
    """

    @staticmethod
    def calculate_oracle_gap(actual_finish: Optional[float], hindsight_best_finish: Optional[float]) -> Optional[float]:
        """
        Computes Oracle Gap (Actual Finish vs Hindsight Best Option).
        """
        if actual_finish is None or hindsight_best_finish is None:
            return None
        return max(0.0, float(actual_finish - hindsight_best_finish))
        
    @staticmethod
    def calculate_expected_regret(actual_finish: Optional[float], expected_finish: Optional[float]) -> Optional[float]:
        """
        Computes Expected Regret (Expected Recommended Finish - Actual Realized Finish).
        (If actual finish is P4, but we expected P2, expected regret is 2.0).
        """
        if actual_finish is None or expected_finish is None:
            return None
        return float(actual_finish - expected_finish)

    @staticmethod
    def calculate_position_mae(expected_positions: List[Optional[float]], actual_positions: List[Optional[float]]) -> Optional[float]:
        """Computes Mean Absolute Error (MAE) between expected and actual finish positions."""
        valid_pairs = [(e, a) for e, a in zip(expected_positions, actual_positions) if e is not None and a is not None]
        if not valid_pairs:
            return None
        e_arr = np.array([e for e, a in valid_pairs])
        a_arr = np.array([a for e, a in valid_pairs])
        return float(np.mean(np.abs(e_arr - a_arr)))

    @staticmethod
    def calculate_strategy_agreement_pct(model_recommendations: List[str], actual_actions: List[str]) -> Optional[float]:
        """Calculates percentage of decision points where model recommendation matches team action."""
        if not model_recommendations or len(model_recommendations) != len(actual_actions):
            return None
        matches = sum(1 for m, a in zip(model_recommendations, actual_actions) if m.lower() in a.lower() or a.lower() in m.lower())
        return float((matches / len(model_recommendations)) * 100.0)

    @staticmethod
    def calculate_brier_score(predicted_probs: List[float], actual_outcomes: List[Optional[int]]) -> Optional[float]:
        """Computes Brier Score for probability calibration assessment."""
        valid_pairs = [(p, o) for p, o in zip(predicted_probs, actual_outcomes) if p is not None and o is not None]
        if not valid_pairs:
            return None
        p_arr = np.array([p for p, o in valid_pairs])
        o_arr = np.array([o for p, o in valid_pairs])
        return float(np.mean((p_arr - o_arr) ** 2))

    @classmethod
    def evaluate_replay_summary(
        cls,
        checkpoints: List[Dict[str, Any]],
        actual_final_finish: Optional[float],
        hindsight_best_finish: Optional[float]
    ) -> Dict[str, Any]:
        """
        Generates complete post-race backtest evaluation summary.
        """
        if not checkpoints:
            return {"error": "Empty replay checkpoints."}

        model_recs = [c.get("model_recommendation", "STAY_OUT") for c in checkpoints]
        actual_acts = [c.get("actual_team_action", "STAY_OUT") for c in checkpoints]
        expected_pos = [c.get("model_expected_finish") for c in checkpoints]
        actual_pos = [actual_final_finish] * len(checkpoints)
        win_probs = [c.get("model_win_prob_pct", 0.0) / 100.0 for c in checkpoints]
        actual_win_flags = [1 if actual_final_finish == 1 else (0 if actual_final_finish is not None else None)] * len(checkpoints)

        oracle_gap = cls.calculate_oracle_gap(actual_final_finish, hindsight_best_finish)
        
        # We calculate expected regret for the last decision point
        final_expected = expected_pos[-1] if expected_pos else None
        expected_regret = cls.calculate_expected_regret(actual_final_finish, final_expected)
        
        mae = cls.calculate_position_mae(expected_pos, actual_pos)
        agreement_pct = cls.calculate_strategy_agreement_pct(model_recs, actual_acts)
        brier = cls.calculate_brier_score(win_probs, actual_win_flags)

        return {
            "total_decision_checkpoints": len(checkpoints),
            "actual_final_finish": actual_final_finish if actual_final_finish is not None else "UNAVAILABLE",
            "hindsight_best_finish": hindsight_best_finish if hindsight_best_finish is not None else "UNAVAILABLE",
            "offline_oracle_gap_positions": round(oracle_gap, 2) if oracle_gap is not None else "UNAVAILABLE",
            "online_expected_regret_positions": round(expected_regret, 2) if expected_regret is not None else "UNAVAILABLE",
            "mean_absolute_position_error": round(mae, 2) if mae is not None else "UNAVAILABLE",
            "strategy_agreement_pct": round(agreement_pct, 1) if agreement_pct is not None else "UNAVAILABLE",
            "brier_calibration_score": round(brier, 4) if brier is not None else "UNAVAILABLE",
            "evaluation_status": "VALIDATED"
        }

