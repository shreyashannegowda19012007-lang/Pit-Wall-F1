"""
Formal Decision Engine for Formula One Strategy Optimization.
Strictly separated from the LLM. Evaluates Monte Carlo simulation outcomes,
applies physical constraints, optimizes against explicit objectives, and outputs
machine-readable StructuredDecision payloads.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import datetime
import uuid

from strategy_model import ObjectiveType, StrategyPlan
from monte_carlo_engine import StochasticSimulationOutcome
from race_state import CompleteRaceState
from bayesian_state import BayesianRaceState


@dataclass
class DecisionConstraint:
    """Strategy constraints enforced by the Decision Engine."""
    min_stops: int = 1
    max_stops: int = 3
    mandatory_compounds_count: int = 2
    max_stint_laps: int = 38
    allowed_compounds: List[str] = field(default_factory=lambda: ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"])


@dataclass
class DecisionAlternative:
    strategy_name: str
    stop_count: int
    win_probability_pct: float
    podium_probability_pct: float
    expected_finish: float
    downside_risk_pct: float
    tradeoff_reason: str


@dataclass
class StructuredDecision:
    """
    Authoritative, machine-readable strategy decision payload produced by the Decision Engine.
    Serves as the strict source of truth for all AI explanations and UI displays.
    """
    decision_id: str
    race_lap: int
    recommended_action: str               # "PIT_NOW", "PIT_IN_N_LAPS", "STAY_OUT"
    recommended_compound: str
    recommended_pit_lap: Optional[int]
    selected_strategy_name: str
    objective: str
    expected_finish: float
    win_probability_pct: float
    podium_probability_pct: float
    downside_risk_pct: float
    primary_reason: str
    supporting_factors: List[str]
    tradeoffs: List[str]
    alternatives: List[DecisionAlternative]
    uncertainties: List[str]
    model_versions: Dict[str, str] = field(default_factory=lambda: {
        "decision_engine": "v2.4.0",
        "monte_carlo": "v2.4.0",
        "bayesian_state": "v2.4.0"
    })
    generated_at: str = field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "race_lap": self.race_lap,
            "recommended_action": self.recommended_action,
            "recommended_compound": self.recommended_compound,
            "recommended_pit_lap": self.recommended_pit_lap,
            "selected_strategy_name": self.selected_strategy_name,
            "objective": self.objective,
            "expected_finish": round(self.expected_finish, 2),
            "win_probability_pct": round(self.win_probability_pct, 1),
            "podium_probability_pct": round(self.podium_probability_pct, 1),
            "downside_risk_pct": round(self.downside_risk_pct, 1),
            "primary_reason": self.primary_reason,
            "supporting_factors": self.supporting_factors,
            "tradeoffs": self.tradeoffs,
            "alternatives": [a.__dict__ for a in self.alternatives],
            "uncertainties": self.uncertainties,
            "model_versions": self.model_versions,
            "generated_at": self.generated_at
        }


class DecisionEngine:
    """
    Deterministic Decision Engine evaluating simulation outcomes against constraints and objectives.
    """

    @classmethod
    def evaluate(
        cls,
        race_state: CompleteRaceState,
        bayesian_state: Optional[BayesianRaceState],
        mc_outcomes: List[StochasticSimulationOutcome],
        objective: str = ObjectiveType.MAX_PODIUM,
        constraints: Optional[DecisionConstraint] = None
    ) -> StructuredDecision:
        """
        Filters invalid strategies, ranks according to objective, and generates a StructuredDecision.
        """
        if constraints is None:
            constraints = DecisionConstraint()

        if not mc_outcomes:
            return cls._fallback_decision(race_state.current_lap, objective)

        # 1. Filter Strategies by Constraints
        valid_outcomes = []
        for outcome in mc_outcomes:
            strat = outcome.strategy_plan
            # Check stop count constraints
            if not (constraints.min_stops <= strat.stop_count <= constraints.max_stops):
                continue
            # Check mandatory compound variety if total stops >= 1
            if strat.stop_count >= 1 and len(set(strat.compounds)) < constraints.mandatory_compounds_count:
                continue
            valid_outcomes.append(outcome)

        if not valid_outcomes:
            valid_outcomes = mc_outcomes  # Fallback to all outcomes if strict filtering eliminates all options

        # 2. Rank Valid Strategies by Objective
        if objective == ObjectiveType.MAX_WIN:
            valid_outcomes.sort(key=lambda x: x.win_probability, reverse=True)
        elif objective == ObjectiveType.MAX_PODIUM:
            valid_outcomes.sort(key=lambda x: x.podium_probability, reverse=True)
        elif objective == ObjectiveType.MIN_POSITION:
            valid_outcomes.sort(key=lambda x: x.expected_position, reverse=False)
        elif objective == ObjectiveType.MIN_RISK:
            valid_outcomes.sort(key=lambda x: x.downside_risk_probability, reverse=False)
        elif objective == ObjectiveType.MIN_RACE_TIME:
            valid_outcomes.sort(key=lambda x: x.expected_race_time_min, reverse=False)
        else:
            valid_outcomes.sort(key=lambda x: x.strategy_score, reverse=True)

        selected = valid_outcomes[0]
        strat_plan = selected.strategy_plan

        # Determine Recommended Action
        if strat_plan.pit_laps and strat_plan.pit_laps[0] == race_state.current_lap + 1:
            rec_action = "PIT_NOW"
            rec_lap = strat_plan.pit_laps[0]
            rec_compound = strat_plan.compounds[1] if len(strat_plan.compounds) > 1 else "MEDIUM"
        elif strat_plan.pit_laps:
            rec_lap = strat_plan.pit_laps[0]
            rec_action = f"PIT_LAP_{rec_lap}"
            rec_compound = strat_plan.compounds[1] if len(strat_plan.compounds) > 1 else "MEDIUM"
        else:
            rec_action = "STAY_OUT"
            rec_lap = None
            rec_compound = strat_plan.compounds[0] if strat_plan.compounds else "MEDIUM"

        # 3. Construct Alternatives
        alternatives: List[DecisionAlternative] = []
        for alt in valid_outcomes[1:3]:
            tradeoff = "Higher win probability but higher downside risk" if alt.win_probability > selected.win_probability else "Lower risk but lower expected finish position"
            alternatives.append(DecisionAlternative(
                strategy_name=alt.strategy_plan.strategy_name,
                stop_count=alt.strategy_plan.stop_count,
                win_probability_pct=round(alt.win_probability * 100.0, 1),
                podium_probability_pct=round(alt.podium_probability * 100.0, 1),
                expected_finish=round(alt.expected_position, 2),
                downside_risk_pct=round(alt.downside_risk_probability * 100.0, 1),
                tradeoff_reason=tradeoff
            ))

        primary_reason = f"Ranks highest under {objective} objective. Delivers {selected.podium_probability*100.0:.1f}% Podium Probability and expected finish of P{selected.expected_position:.1f}."

        supporting_factors = [
            f"Simulated Podium Probability: {selected.podium_probability*100.0:.1f}% across N={selected.iterations:,} Monte Carlo runs",
            f"Expected Race Time: {selected.expected_race_time_min:.2f} min (95% interval: [{selected.race_time_p2_5_min:.2f} - {selected.race_time_p97_5_min:.2f}] min)",
            f"Downside Risk (P10+): {selected.downside_risk_probability*100.0:.1f}%"
        ]

        tradeoffs = [
            f"Sacrifices {max(0.0, (max([x.win_probability for x in valid_outcomes]) - selected.win_probability)*100.0):.1f}% peak win probability to optimize overall podium consistency"
        ]

        uncertainties = [
            "Stochastic Safety Car / VSC timing probability",
            "Bayesian posterior tyre degradation rate uncertainty",
            "Pit lane traffic congestion delays"
        ]

        return StructuredDecision(
            decision_id=f"DEC-{uuid.uuid4().hex[:8].upper()}",
            race_lap=race_state.current_lap,
            recommended_action=rec_action,
            recommended_compound=rec_compound,
            recommended_pit_lap=rec_lap,
            selected_strategy_name=strat_plan.strategy_name,
            objective=objective,
            expected_finish=selected.expected_position,
            win_probability_pct=selected.win_probability * 100.0,
            podium_probability_pct=selected.podium_probability * 100.0,
            downside_risk_pct=selected.downside_risk_probability * 100.0,
            primary_reason=primary_reason,
            supporting_factors=supporting_factors,
            tradeoffs=tradeoffs,
            alternatives=alternatives,
            uncertainties=uncertainties
        )

    @classmethod
    def _fallback_decision(cls, race_lap: int, objective: str) -> StructuredDecision:
        return StructuredDecision(
            decision_id=f"DEC-FALLBACK-{race_lap}",
            race_lap=race_lap,
            recommended_action="UNAVAILABLE",
            recommended_compound="UNKNOWN",
            recommended_pit_lap=None,
            selected_strategy_name="Degraded Mode",
            objective=objective,
            expected_finish=0.0,
            win_probability_pct=0.0,
            podium_probability_pct=0.0,
            downside_risk_pct=0.0,
            primary_reason="Simulation data absent or invalid. Strategy decision degraded/unavailable.",
            supporting_factors=["Missing Monte Carlo outcomes"],
            tradeoffs=[],
            alternatives=[],
            uncertainties=["Simulation unavailable"]
        )

