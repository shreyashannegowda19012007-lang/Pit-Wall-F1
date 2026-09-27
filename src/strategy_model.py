"""
Strategy Representation & Multi-Objective Optimization Model.
Supports 1-stop, 2-stop, 3-stop, and multi-objective strategy ranking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


class ObjectiveType:
    MAX_WIN = "MAX_WIN_PROBABILITY"           # Aggressive win optimization
    MAX_PODIUM = "MAX_PODIUM_PROBABILITY"     # Balanced podium optimization (Default)
    MIN_POSITION = "MIN_EXPECTED_POSITION"   # Optimal average position
    MIN_RISK = "MIN_DOWNSIDE_RISK"            # Conservative risk minimization (P10 or worse %)
    MIN_RACE_TIME = "MIN_RACE_TIME"           # Pure expected race time minimization


@dataclass
class StintPlan:
    compound: str           # "SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"
    start_lap: int
    target_laps: int


@dataclass
class StrategyPlan:
    """
    Explicit multi-stint strategy plan.
    """
    strategy_name: str
    stints: List[StintPlan]
    pit_laps: List[int]
    compounds: List[str]
    stop_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "stop_count": self.stop_count,
            "pit_laps": self.pit_laps,
            "compounds": self.compounds,
            "stint_count": len(self.stints)
        }
