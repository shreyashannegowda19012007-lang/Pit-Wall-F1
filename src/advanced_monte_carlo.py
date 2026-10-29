"""
Advanced Production-Grade Monte Carlo Strategy Engine (Phases 1-75).
Implements formal strategy candidates with FIA rule validation, stochastic uncertainty sampling
(tyre degradation, pit stop LogNormal distribution, Safety Car timing, weather), variable sample sizes
(100 to 5,000+), 95% Monte Carlo confidence intervals, full finishing position distributions P1..P20,
strategy regret analysis, robustness scores, multi-objective ranking, probability calibration (Brier score),
unified full-field probability benchmark, and 1-factor sensitivity analysis.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import math

from full_field_simulator import FullFieldRaceSimulator, RaceSimulationConfig
from tyre_engine import EmpiricalTyreModel


@dataclass
class StrategyCandidate:
    strategy_id: str
    name: str
    pit_laps: List[int]
    compounds: List[str]
    pit_window_start: int
    pit_window_end: int
    safety_car_response: str     # "PIT_IMMEDIATELY", "STAY_OUT", "STANDARD"
    weather_response: str        # "SWITCH_INTERMEDIATE", "STAY_SLICK"
    is_fia_valid: bool = True
    description: str = ""


@dataclass
class StrategyMonteCarloResult:
    strategy_id: str
    name: str
    num_simulations: int
    win_probability_pct: float
    win_ci_95_pct: Tuple[float, float]
    podium_probability_pct: float
    points_probability_pct: float
    expected_finish_position: float
    finish_position_std: float
    p5_position: int
    p95_position: int
    finish_position_distribution: Dict[int, float]  # P1..P20 probabilities
    mean_race_time_s: float
    race_time_std_s: float
    strategy_regret_s: float
    robustness_score: float
    risk_score: float
    brier_calibration_score: float
    is_recommended: bool


class AutomatedCandidateGenerator:
    """
    Generates and validates plausible FIA-compliant pit strategies dynamically
    scaled to the actual race lap count and circuit demands.
    """

    @classmethod
    def generate_valid_candidates(cls, total_laps: int = 66, target_driver: str = "VER") -> List[StrategyCandidate]:
        """
        Generates 1-Stop, 2-Stop, and 3-Stop candidate strategies sized to total_laps.
        Validates FIA rule (minimum 2 distinct dry compounds used in dry race).
        """
        candidates: List[StrategyCandidate] = []

        # Key stint transition points scaled to total_laps
        p1_2s = max(2, int(round(total_laps * 0.27)))
        p2_2s = max(p1_2s + 2, int(round(total_laps * 0.67)))

        p1_inv = max(2, int(round(total_laps * 0.36)))
        p2_inv = max(p1_inv + 2, int(round(total_laps * 0.70)))

        mid_1s = max(2, int(round(total_laps * 0.45)))
        late_1s = max(mid_1s + 2, int(round(total_laps * 0.58)))
        early_1s = max(2, int(round(total_laps * 0.30)))

        p1_3s = max(2, int(round(total_laps * 0.23)))
        p2_3s = max(p1_3s + 2, int(round(total_laps * 0.48)))
        p3_3s = max(p2_3s + 2, int(round(total_laps * 0.74)))

        # 1. 2-Stop Soft -> Medium -> Soft (Verstappen 2024 Spanish GP winning blueprint)
        candidates.append(StrategyCandidate(
            strategy_id="OPT-2S-SMS",
            name="2-Stop Soft -> Medium -> Soft",
            pit_laps=[p1_2s, p2_2s],
            compounds=["SOFT", "MEDIUM", "SOFT"],
            pit_window_start=max(1, p1_2s - 3),
            pit_window_end=min(total_laps - 2, p2_2s + 3),
            safety_car_response="PIT_IMMEDIATELY",
            weather_response="SWITCH_INTERMEDIATE",
            is_fia_valid=True,
            description=f"Aggressive high-grip sprint pitting on Laps {p1_2s} & {p2_2s}"
        ))

        # 2. 2-Stop Soft -> Medium -> Hard (Balanced attack & durability)
        p2_smh = max(p1_2s + 2, int(round(total_laps * 0.64)))
        candidates.append(StrategyCandidate(
            strategy_id="OPT-2S-SMH",
            name="2-Stop Soft -> Medium -> Hard",
            pit_laps=[p1_2s, p2_smh],
            compounds=["SOFT", "MEDIUM", "HARD"],
            pit_window_start=max(1, p1_2s - 3),
            pit_window_end=min(total_laps - 2, p2_smh + 3),
            safety_car_response="PIT_IMMEDIATELY",
            weather_response="SWITCH_INTERMEDIATE",
            is_fia_valid=True,
            description=f"Balanced 2-Stop pitting on Laps {p1_2s} & {p2_smh}"
        ))

        # 3. 2-Stop Medium -> Soft -> Hard (Inverted opening stint)
        candidates.append(StrategyCandidate(
            strategy_id="OPT-2S-MSH",
            name="2-Stop Medium -> Soft -> Hard",
            pit_laps=[p1_inv, p2_inv],
            compounds=["MEDIUM", "SOFT", "HARD"],
            pit_window_start=max(1, p1_inv - 3),
            pit_window_end=min(total_laps - 2, p2_inv + 3),
            safety_car_response="PIT_IMMEDIATELY",
            weather_response="SWITCH_INTERMEDIATE",
            is_fia_valid=True,
            description=f"Alternative 2-Stop with Medium opening stint pitting Laps {p1_inv} & {p2_inv}"
        ))

        # 4. 1-Stop Medium -> Hard (Track position defense)
        candidates.append(StrategyCandidate(
            strategy_id="OPT-1S-MH",
            name="1-Stop Medium -> Hard",
            pit_laps=[mid_1s],
            compounds=["MEDIUM", "HARD"],
            pit_window_start=max(1, mid_1s - 4),
            pit_window_end=min(total_laps - 2, mid_1s + 4),
            safety_car_response="PIT_IMMEDIATELY",
            weather_response="SWITCH_INTERMEDIATE",
            is_fia_valid=True,
            description=f"Track position 1-Stop pitting on Lap {mid_1s}"
        ))

        # 5. 1-Stop Hard -> Medium (Overcut / long first stint)
        candidates.append(StrategyCandidate(
            strategy_id="OPT-1S-HM",
            name="1-Stop Hard -> Medium (Overcut)",
            pit_laps=[late_1s],
            compounds=["HARD", "MEDIUM"],
            pit_window_start=max(1, late_1s - 3),
            pit_window_end=min(total_laps - 2, late_1s + 5),
            safety_car_response="STAY_OUT",
            weather_response="SWITCH_INTERMEDIATE",
            is_fia_valid=True,
            description=f"Overcut 1-Stop starting on Hard pitting Lap {late_1s}"
        ))

        # 6. 3-Stop Soft -> Medium -> Soft -> Soft (Maximum pace sprint for high degradation tracks)
        if total_laps >= 35:
            candidates.append(StrategyCandidate(
                strategy_id="OPT-3S-SMSS",
                name="3-Stop Soft -> Medium -> Soft -> Soft",
                pit_laps=[p1_3s, p2_3s, p3_3s],
                compounds=["SOFT", "MEDIUM", "SOFT", "SOFT"],
                pit_window_start=max(1, p1_3s - 2),
                pit_window_end=min(total_laps - 2, p3_3s + 2),
                safety_car_response="PIT_IMMEDIATELY",
                weather_response="SWITCH_INTERMEDIATE",
                is_fia_valid=True,
                description=f"3-Stop maximum grip sprint pitting on Laps {p1_3s}, {p2_3s}, & {p3_3s}"
            ))

        # FIA Rule Validation: Ensure at least 2 distinct dry compounds used
        valid_candidates = []
        for c in candidates:
            if len(set(c.compounds)) >= 2:
                # Verify pit stops match stint transitions and all laps < total_laps
                if len(c.pit_laps) == len(c.compounds) - 1:
                    if all(0 < lap < total_laps for lap in c.pit_laps):
                        c.is_fia_valid = True
                        valid_candidates.append(c)

        return valid_candidates


class AdvancedMonteCarloStrategyEngine:
    """
    Production-Grade Probabilistic Strategy Engine evaluating candidate pit strategies (Phases 1-75).
    """

    @classmethod
    def evaluate_strategy_candidates(
        cls,
        target_driver_id: str = "VER",
        circuit_id: str = "SPAIN",
        total_laps: int = 66,
        num_simulations_per_candidate: int = 250,
        base_seed: int = 42,
        candidates: Optional[List[StrategyCandidate]] = None,
        objective: str = "BALANCED",
        season: int = 2025,
        evaluation_mode: str = "PRE_RACE",
        user_deg_multiplier: float = 1.0,
        user_pit_loss_offset_s: float = 0.0,
        user_sc_prob_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes N Monte Carlo iterations per strategy candidate using Common Random Numbers (CRN),
        sampling stochastic distributions (Safety Car, traffic, pit stop durations), computing Win/Podium CIs,
        Strategy Regret, Robustness, Brier calibration, multi-objective ranking, and reconciled Full-Field Benchmark.
        Delegates to the authoritative GlobalStrategyEngine.
        """
        from global_strategy_engine import GlobalStrategyEngine
        return GlobalStrategyEngine.run_global_simulation(
            target_driver=target_driver_id,
            circuit_id=circuit_id,
            season=season,
            total_laps=total_laps,
            num_sims=num_simulations_per_candidate,
            objective=objective,
            evaluation_mode=evaluation_mode,
            random_seed=base_seed,
            user_deg_multiplier=user_deg_multiplier,
            user_pit_loss_offset_s=user_pit_loss_offset_s,
            user_sc_prob_override=user_sc_prob_override,
            candidates=candidates
        )
