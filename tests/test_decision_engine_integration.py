import pytest
import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from src.monte_carlo_engine import MonteCarloRaceEngine
from src.decision_engine import DecisionEngine, DecisionConstraint
from src.race_state import CompleteRaceState, DriverState, TyreState, FuelState, WeatherState, TrackState, SafetyCarState
from src.strategy_model import ObjectiveType

def test_decision_engine_integration():
    # 1. Setup real test data
    tyre_state_target = TyreState(compound="MEDIUM", age_laps=15, remaining_grip_pct=60.0, thermal_deg_rate=0.08)
    fuel_state = FuelState(fuel_remaining_kg=80.0)
    target_driver = DriverState(driver_id="VER", position=1, current_gap_to_leader_s=0.0, base_pace_s=88.5, tyre_state=tyre_state_target, fuel_state=fuel_state)
    
    tyre_state_opp = TyreState(compound="HARD", age_laps=5, remaining_grip_pct=85.0, thermal_deg_rate=0.04)
    opp_driver = DriverState(driver_id="HAM", position=2, current_gap_to_leader_s=1.2, base_pace_s=88.7, tyre_state=tyre_state_opp, fuel_state=fuel_state)
    
    race_state = CompleteRaceState(
        current_lap=30,
        total_laps=57,
        drivers={"VER": target_driver, "HAM": opp_driver},
        weather=WeatherState(),
        track=TrackState(pit_lane_loss_seconds=22.0),
        safety_car=SafetyCarState()
    )

    # 2. Strategy Engine Executes
    mc_engine = MonteCarloRaceEngine(iterations=100, seed=42) # reduced iterations for test speed
    
    # 3. Candidate strategies generated
    mc_outcomes = mc_engine.rank_strategies(
        target_driver=target_driver,
        opponents=[opp_driver],
        race_state=race_state,
        objective=ObjectiveType.MAX_PODIUM
    )

    assert len(mc_outcomes) > 0, "Monte Carlo engine failed to generate candidate strategies"
    
    # 4. Decision Engine receives them and selects a recommendation
    struct_decision = DecisionEngine.evaluate(
        race_state=race_state,
        bayesian_state=None,
        mc_outcomes=mc_outcomes,
        objective=ObjectiveType.MAX_WIN,
        constraints=DecisionConstraint(min_stops=0)
    )

    # 5. Recommendation contains actual calculated values
    assert struct_decision is not None, "Decision Engine returned None"
    assert struct_decision.recommended_action in ["STAY_OUT", "PIT_NOW", "PIT_IN_N_LAPS", "PIT_LAP_45", "PIT_LAP_48", "PIT_LAP_32", "PIT_LAP_42"] or struct_decision.recommended_action.startswith("PIT_LAP"), f"Invalid action: {struct_decision.recommended_action}"
    assert struct_decision.win_probability_pct >= 0.0, "Win probability must be a valid float"
    assert struct_decision.expected_finish >= 1.0, "Expected finish must be >= 1"
    
    print("\n--- ACTUAL STRATEGY OUTPUT ---")
    print(f"Recommended Strategy: {struct_decision.selected_strategy_name}")
    print(f"Action: {struct_decision.recommended_action}")
    print(f"Pit Lap: {struct_decision.recommended_pit_lap}")
    print(f"Compound: {struct_decision.recommended_compound}")
    print(f"Expected Finish: P{struct_decision.expected_finish:.1f}")
    print(f"Win Probability: {struct_decision.win_probability_pct:.1f}%")
    print(f"Podium Probability: {struct_decision.podium_probability_pct:.1f}%")
    print(f"Downside Risk: {struct_decision.downside_risk_pct:.1f}%")
    print(f"Primary Reason: {struct_decision.primary_reason}")
    print(f"Model Versions: {struct_decision.model_versions}")
    print("------------------------------")
