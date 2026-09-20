"""
Authoritative Strategy Engine — Architecture Documentation & Production Routing.

This module documents the three Monte Carlo engine architecture and provides
the canonical production routing for strategy computation.

=============================================================================
THREE MONTE CARLO ENGINES — DISTINCT RESPONSIBILITIES
=============================================================================

1. MonteCarloRaceEngine (monte_carlo_engine.py)
   --------------------------------------------------
   PURPOSE: Single-driver, single-strategy probability estimation.
   USE FOR: - Per-strategy win/podium/points probability distributions
            - Expected race time intervals (P2.5 / P97.5)
            - Position probability maps (P1..P20)
            - Sensitivity analysis (OAT parameter perturbation)
   ALGORITHM: Fully vectorized NumPy arrays (N=1000-10000 iterations)
   OUTPUT: StochasticSimulationOutcome (per-strategy)
   UI USAGE: "Strategy" tab → Monte Carlo HUD, sensitivity analysis

2. AdvancedMonteCarloStrategyEngine (advanced_monte_carlo.py)
   --------------------------------------------------
   PURPOSE: Multi-candidate strategy comparison with regret analysis.
   USE FOR: - Comparing 2+ strategy candidates (1-stop vs 2-stop etc.)
            - Safety car response scenario evaluation
            - Weather scenario branch analysis
            - Regret quantification (opportunity cost of wrong strategy)
            - Pareto frontier strategy ranking
            - Brier score calibration of strategy probabilities
   ALGORITHM: Uses FullFieldRaceSimulator for each candidate
   OUTPUT: StrategyMonteCarloResult (per-candidate) + Pareto ranking
   UI USAGE: "Advanced Strategy" tab → candidate comparison

3. FullFieldRaceSimulator (full_field_simulator.py)
   --------------------------------------------------
   PURPOSE: Full 20-car field race simulation (all drivers as agents).
   USE FOR: - Full-field finishing position distributions for all 20 cars
            - Rival behaviour modelling (aggression, pace variance)
            - Track battle simulation (DRS trains, traffic effects)
            - Championship points probability across the season
   ALGORITHM: Per-lap event loop with all 20 drivers interacting
   OUTPUT: FullFieldSimulationResult (all 20 drivers' distributions)
   UI USAGE: "Full Field" tab → 20-car timing tower, race outcome map

=============================================================================
PRODUCTION ROUTING DECISION
=============================================================================

                        User Action
                           │
          ┌────────────────┴──────────────────┐
          │                                   │
   "Simulate MY strategy"           "Full field race prediction"
          │                                   │
          ▼                                   ▼
  MonteCarloRaceEngine            FullFieldRaceSimulator
  (single driver focus)          (all 20 drivers as agents)
          │
          │  "Compare all strategy candidates"
          ▼
  AdvancedMonteCarloStrategyEngine
  (multi-candidate + regret)

=============================================================================
IMPORTANT: The UI must not label all three as the same "Monte Carlo engine."
- The Strategy tab uses MonteCarloRaceEngine
- The Advanced Strategy tab uses AdvancedMonteCarloStrategyEngine
- The Full Field tab uses FullFieldRaceSimulator
=============================================================================
"""

try:
    from .decision_architecture import (
        DriverContext,
        RaceContext,
        StrategyRecommendation,
        DecisionEngine,
        JarvisEvidenceEngine,
        DecisionArchitectureOrchestrator
    )
except ImportError:
    from decision_architecture import (
        DriverContext,
        RaceContext,
        StrategyRecommendation,
        DecisionEngine,
        JarvisEvidenceEngine,
        DecisionArchitectureOrchestrator
    )

# Production strategy path: DecisionArchitectureOrchestrator orchestrates
# strategy recommendation via DecisionEngine and evidence from JarvisEvidenceEngine.
# Monte Carlo probability quantification uses MonteCarloRaceEngine internally.

__all__ = [
    'DriverContext',
    'RaceContext',
    'StrategyRecommendation',
    'DecisionEngine',
    'JarvisEvidenceEngine',
    'DecisionArchitectureOrchestrator'
]
