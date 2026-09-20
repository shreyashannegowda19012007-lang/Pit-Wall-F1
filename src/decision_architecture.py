import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

# =============================================================================
# 1 & 2. CANONICAL CONTEXTS
# =============================================================================

@dataclass
class DriverContext:
    """Canonical representation of a single driver's state."""
    driver: str
    team: str
    position: int
    gap_to_leader: float
    interval_to_ahead: float
    lap: int
    last_lap_s: float
    best_lap_s: float
    tyre_compound: str
    tyre_age_laps: int
    pit_status: str
    degradation_estimate_s_per_lap: float
    telemetry_state: str

@dataclass
class RaceContext:
    """Canonical representation of the entire race/session state."""
    season: int
    round: int
    event: str
    session: str
    current_lap: int
    total_laps: int
    drivers: Dict[str, DriverContext]
    telemetry_availability: bool
    model_availability: Dict[str, bool]
    data_timestamp: str

# =============================================================================
# 15. DECISION ENGINE
# =============================================================================

@dataclass
class StrategyRecommendation:
    recommendation: str
    expected_race_time_s: float
    p_win: float
    p_podium: float
    confidence_pct: float
    primary_reason: str
    alternative: str
    risk: str
    evidence_refs: List[str]
    model_versions: Dict[str, str]
    timestamp: str
    assumptions: Dict[str, Any]
    uncertainty: Dict[str, float]
    strategy_regret_s: float
    disagreement_analysis: str

class DecisionEngine:
    """
    Authoritative strategy recommendation layer.
    """
    
    @classmethod
    def generate_recommendation(
        cls, 
        race_context: RaceContext, 
        primary_driver: str,
        comp_driver: str
    ) -> StrategyRecommendation:
        from src.rl_strategy_agent import RLStrategyEvaluator
        from src.race_state import CompleteRaceState, DriverState, TyreState, FuelState, WeatherState, TrackState, SafetyCarState
        from src.monte_carlo_engine import MonteCarloRaceEngine
        from src.decision_engine import DecisionEngine as FormalDecisionEngine
        import os
        from src import config
        
        models_used = {"DecisionEngine": "v2.0", "MonteCarlo": "v2.4.0"}
        
        from src.rl_config import is_rl_enabled
        
        # Check RL Availability ONLY if explicitly enabled
        rl_available = False
        rl_installed = os.path.exists(os.path.join(config.BASE_DIR, "models", "rl_strategy", "ppo_strategy_v1.zip"))
        
        if is_rl_enabled():
            if rl_installed:
                rl_available = True
                models_used["RL_PPO"] = "ppo_strategy_v1"
            
        # Check ML Availability
        ml_available = False
        ml_model_path = os.path.join(config.BASE_DIR, "models", "lap_time", "xgboost_lap_time_v1.json")
        if os.path.exists(ml_model_path):
            ml_available = True
            models_used["ML_XGBoost"] = "xgboost_lap_time_v1"

        if not race_context.telemetry_availability:
            # Fallback if no real data
            return cls._fallback_recommendation(primary_driver, models_used)

        p_ctx = race_context.drivers.get(primary_driver)
        if not p_ctx:
            return cls._fallback_recommendation(primary_driver, models_used)

        # 1. Build formal states for Monte Carlo
        t_driver_state = DriverState(
            driver_id=primary_driver,
            position=p_ctx.position,
            current_gap_to_leader_s=p_ctx.gap_to_leader,
            base_pace_s=p_ctx.last_lap_s if p_ctx.last_lap_s > 0 else 82.0,
            tyre_state=TyreState(compound=p_ctx.tyre_compound, age_laps=p_ctx.tyre_age_laps, remaining_grip_pct=90.0, thermal_deg_rate=0.08),
            fuel_state=FuelState(fuel_remaining_kg=100.0)
        )
        
        opp_states = []
        for d_id, d_ctx in race_context.drivers.items():
            if d_id != primary_driver:
                opp_states.append(DriverState(
                    driver_id=d_id,
                    position=d_ctx.position,
                    current_gap_to_leader_s=d_ctx.gap_to_leader,
                    base_pace_s=d_ctx.last_lap_s if d_ctx.last_lap_s > 0 else 82.0,
                    tyre_state=TyreState(compound=d_ctx.tyre_compound, age_laps=d_ctx.tyre_age_laps, remaining_grip_pct=90.0, thermal_deg_rate=0.08),
                    fuel_state=FuelState(fuel_remaining_kg=100.0)
                ))
                
        c_race_state = CompleteRaceState(
            current_lap=race_context.current_lap,
            total_laps=race_context.total_laps,
            drivers={d.driver_id: d for d in [t_driver_state] + opp_states},
            weather=WeatherState(),
            track=TrackState(total_laps=race_context.total_laps),
            safety_car=SafetyCarState()
        )
        
        # 2. Strategy Candidate Generation & Monte Carlo Optimizer
        mc_engine = MonteCarloRaceEngine(iterations=25, seed=42)
        mc_rankings = mc_engine.rank_strategies(t_driver_state, opp_states, c_race_state, objective="MAX_PODIUM")
        
        # 3. Decision Engine (Mapping MC to Formal Decision)
        structured_dec = FormalDecisionEngine.evaluate(c_race_state, None, mc_rankings, objective="MAX_PODIUM")
        
        recommendation = structured_dec.recommended_action
        reasoning = structured_dec.primary_reason
        alternative = structured_dec.alternatives[0].strategy_name if structured_dec.alternatives else "Stay Out"
        risk = f"Downside Risk: {structured_dec.downside_risk_pct}%"
        mc_regret = 0.0
        if mc_rankings:
            best_time = min(r.expected_race_time_min for r in mc_rankings)
            mc_regret = (mc_rankings[0].expected_race_time_min - best_time) * 60.0
        
        expected_time_s = mc_rankings[0].expected_race_time_min * 60.0 if mc_rankings else float(race_context.total_laps * t_driver_state.base_pace_s)

        # 4. Experimental RL Override (Only if explicitly enabled)
        if rl_available and is_rl_enabled():
            eval_res = RLStrategyEvaluator.evaluate_rl_vs_baselines(primary_driver, race_context.total_laps)
            rl_action = eval_res.get("rl_agent", {}).get("recommended_action", "UNAVAILABLE")
            if rl_action != "UNAVAILABLE":
                recommendation = rl_action
                reasoning = f"[EXPERIMENTAL RL OVERRIDE] RL policy model recommends {rl_action}."
                mc_regret = eval_res.get("rl_agent", {}).get("strategy_regret_s", 0.0)

        confidence = max(0.0, 100.0 - structured_dec.downside_risk_pct) if mc_rankings else 0.0
        
        return StrategyRecommendation(
            recommendation=recommendation,
            expected_race_time_s=expected_time_s,
            p_win=structured_dec.win_probability_pct,
            p_podium=structured_dec.podium_probability_pct,
            confidence_pct=confidence,
            primary_reason=reasoning,
            alternative=alternative,
            risk=risk,
            evidence_refs=[f"Lap {race_context.current_lap} Race State", "Monte Carlo Simulator"],
            model_versions=models_used,
            timestamp=datetime.now(timezone.utc).isoformat(),
            assumptions={"track_evolution": "Normal"},
            uncertainty={"lap_time_std": 0.4},
            strategy_regret_s=mc_regret,
            disagreement_analysis=""
        )
        
    @classmethod
    def _fallback_recommendation(cls, driver: str, models: Dict[str, str]) -> StrategyRecommendation:
         return StrategyRecommendation(
            recommendation="UNAVAILABLE",
            expected_race_time_s=0.0,
            p_win=0.0, p_podium=0.0,
            confidence_pct=0.0,
            primary_reason="No canonical telemetry data available to make decision.",
            alternative="N/A", risk="N/A", evidence_refs=[],
            model_versions=models,
            timestamp=datetime.now(timezone.utc).isoformat(),
            assumptions={}, uncertainty={}, strategy_regret_s=0.0, disagreement_analysis=""
        )

# =============================================================================
# 19. JARVIS EVIDENCE LAYER
# =============================================================================

class JarvisEvidenceEngine:
    
    @classmethod
    def construct_jarvis_context(
        cls,
        race_context: RaceContext,
        primary_driver: str,
        comparison_driver: str,
        recommendation: StrategyRecommendation,
        time_loss_insights: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Builds evidence payload to enforce NO HALLUCINATION in JARVIS."""
        pd_ctx = race_context.drivers.get(primary_driver)
        cd_ctx = race_context.drivers.get(comparison_driver)
        
        return {
            "mode": "REPLAY" if race_context.season < 2026 else "LIVE", 
            "primary_driver": asdict(pd_ctx) if pd_ctx else None,
            "comparison_driver": asdict(cd_ctx) if cd_ctx else None,
            "decision_engine_recommendation": asdict(recommendation),
            "telemetry_insights": time_loss_insights,
            "model_status": race_context.model_availability
        }

# =============================================================================
# API INTEGRATION
# =============================================================================

class DecisionArchitectureOrchestrator:
    """Orchestrates the canonical R6 integration flow."""
    
    @classmethod
    def build_race_context(cls, session_id: str = "S-2024-SPAIN", timestamp_s: float = 1200.0, mode: str = "REPLAY") -> RaceContext:
        """Fetches from RealtimeRaceStateEngine to build Canonical RaceContext."""
        from src.realtime_race_state import RealtimeRaceStateEngine
        
        state_dict = RealtimeRaceStateEngine.get_unified_state(session_id, timestamp_s, mode)
        
        season = state_dict.get("session_info", {}).get("year", 2024)
        round_n = state_dict.get("session_info", {}).get("round", 1)
        event = state_dict.get("session_info", {}).get("event_name", "Grand Prix")
        session = state_dict.get("session_info", {}).get("session", "Race")
        
        current_lap = state_dict.get("timing_tower", {}).get("current_lap", 1)
        total_laps = state_dict.get("timing_tower", {}).get("total_laps", 57)
        
        drivers_dict = {}
        for d in state_dict.get("timing_tower", {}).get("drivers", []):
            d_id = d.get("driver_id", "UNK")
            drivers_dict[d_id] = DriverContext(
                driver=d_id,
                team=d.get("team", "Unknown"),
                position=d.get("position", 0),
                gap_to_leader=d.get("gap_to_leader_s", 0.0),
                interval_to_ahead=d.get("interval_to_ahead_s", 0.0),
                lap=d.get("current_lap", current_lap),
                last_lap_s=d.get("last_lap_time_s", 0.0),
                best_lap_s=d.get("best_lap_time_s", 0.0),
                tyre_compound=d.get("tyre_compound", "UNKNOWN"),
                tyre_age_laps=d.get("tyre_age_laps", 0),
                pit_status=d.get("pit_status", "TRACK"),
                degradation_estimate_s_per_lap=0.0,
                telemetry_state="AVAILABLE" if d.get("last_lap_time_s", 0.0) > 0 else "NO_DATA"
            )
            
        import os
        from src import config
        from src.rl_config import is_rl_enabled
        
        rl_installed = os.path.exists(os.path.join(config.BASE_DIR, "models", "rl_strategy", "ppo_strategy_v1.zip"))
        rl_enabled = is_rl_enabled()
        
        model_availability = {
            "RL_installed": rl_installed,
            "RL_experimental_enabled": rl_enabled,
            "RL": rl_installed and rl_enabled,
            "ML": os.path.exists(os.path.join(config.BASE_DIR, "models", "lap_time", "xgboost_lap_time_v1.json")),
        }
            
        return RaceContext(
            season=season, round=round_n, event=event, session=session,
            current_lap=current_lap, total_laps=total_laps,
            drivers=drivers_dict,
            telemetry_availability=state_dict.get("provider") != "FALLBACK",
            model_availability=model_availability,
            data_timestamp=datetime.now(timezone.utc).isoformat()
        )


