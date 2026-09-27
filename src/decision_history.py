"""
Decision Timeline, Audit Trail & Human Override Persistence Engine.
Persists structured decision snapshots lap-by-lap, tracks human engineer overrides,
and provides comparative delta analysis to answer "Why did the decision change?".
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import datetime

from decision_engine import StructuredDecision


@dataclass
class HumanOverrideRecord:
    """Record of an explicit human engineer strategy override."""
    lap_number: int
    original_recommendation: str
    human_choice: str
    override_reason: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lap_number": self.lap_number,
            "original_recommendation": self.original_recommendation,
            "human_choice": self.human_choice,
            "override_reason": self.override_reason,
            "timestamp": self.timestamp
        }


class DecisionAuditTrail:
    """
    Central manager for decision snapshot persistence, audit trails, and comparative deltas.
    """

    def __init__(self):
        self.snapshots: Dict[int, StructuredDecision] = {}
        self.human_overrides: List[HumanOverrideRecord] = []

    def record_decision(self, decision: StructuredDecision):
        """Records structured decision snapshot at specified lap."""
        self.snapshots[decision.race_lap] = decision

    def record_human_override(self, lap_number: int, original_rec: str, human_choice: str, reason: str) -> HumanOverrideRecord:
        """Records an explicit human override."""
        rec = HumanOverrideRecord(
            lap_number=lap_number,
            original_recommendation=original_rec,
            human_choice=human_choice,
            override_reason=reason
        )
        self.human_overrides.append(rec)
        return rec

    def get_decision(self, lap_number: int) -> Optional[StructuredDecision]:
        """Retrieves exact structured decision snapshot at specified lap."""
        return self.snapshots.get(lap_number)

    def compare_decisions(self, lap_a: int, lap_b: int) -> Dict[str, Any]:
        """
        Compares decision snapshots at lap A vs lap B to explain why the recommendation changed.
        """
        dec_a = self.snapshots.get(lap_a)
        dec_b = self.snapshots.get(lap_b)

        if not dec_a or not dec_b:
            return {
                "comparable": False,
                "reason": f"Missing decision snapshot for lap {lap_a} or lap {lap_b}."
            }

        strategy_changed = dec_a.selected_strategy_name != dec_b.selected_strategy_name
        podium_delta_pct = dec_b.podium_probability_pct - dec_a.podium_probability_pct
        win_delta_pct = dec_b.win_probability_pct - dec_a.win_probability_pct
        position_delta = dec_b.expected_finish - dec_a.expected_finish

        explanation = (
            f"At Lap {lap_b}, the recommendation shifted from '{dec_a.selected_strategy_name}' to '{dec_b.selected_strategy_name}'. "
            f"Podium probability shifted by {podium_delta_pct:+.1f}% ({dec_a.podium_probability_pct:.1f}% -> {dec_b.podium_probability_pct:.1f}%). "
            f"Expected finish shifted by {position_delta:+.2f} places."
        ) if strategy_changed else (
            f"Recommendation remained constant ('{dec_a.selected_strategy_name}'). "
            f"Podium probability shifted by {podium_delta_pct:+.1f}% across laps {lap_a}-{lap_b}."
        )

        return {
            "comparable": True,
            "lap_a": lap_a,
            "lap_b": lap_b,
            "strategy_changed": strategy_changed,
            "strategy_a": dec_a.selected_strategy_name,
            "strategy_b": dec_b.selected_strategy_name,
            "podium_delta_pct": round(podium_delta_pct, 1),
            "win_delta_pct": round(win_delta_pct, 1),
            "position_delta": round(position_delta, 2),
            "explanation": explanation
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_laps": list(self.snapshots.keys()),
            "snapshots_count": len(self.snapshots),
            "human_overrides": [h.to_dict() for h in self.human_overrides]
        }


# Global Decision Audit Trail Singleton
global_decision_audit = DecisionAuditTrail()
