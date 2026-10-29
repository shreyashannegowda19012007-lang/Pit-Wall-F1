# Pitwall F1 Backend Analytical Model & Integration Audit

**Audit Date**: October 2026  
**Status**: Comprehensive In-Progress Audit & Repair  
**Target Architecture**: FastF1 + OpenF1 Authoritative Platform (FastAPI Backend + React Frontend)

---

## 1. Inventory & Traceability Matrix

| Component / Subsystem | Primary Module(s) | Input Schema | Output Schema | Provenance | Defect Status | Fix Status | Test Status |
|---|---|---|---|---|---|---|---|
| **Tyre Analytics & Degradation** | `src/tyre_analytics.py`, `src/unified_tyre_intelligence.py`, `src/tyre_engine.py` | FastF1 Lap Telemetry (`LapTime`, `TyreLife`, `Compound`, `Stint`) | Degradation slope (s/lap), fuel-corrected times, R², Bayesian posterior | FastF1 session laps | **Defect 1**: Dict unpacking bug in `unified_tyre_intelligence.py`<br>**Defect 2**: Key mismatch in callers (`estimated_degradation_per_lap` vs `degradation_slope_s_per_lap`) | Identified | Pending Fix |
| **Strategy & Undercut Optimizer** | `src/probabilistic_service.py`, `src/authoritative_strategy_engine.py` | Target/Rival driver IDs, gap (s), base pace (s), laps | Undercut/Overcut P(win), expected delta gain (s), recommendation | FastF1 lap timing differentials & Monte Carlo simulations | **Defect 3**: Hardcoded `cur_lap=22, total_laps=66, age=15`<br>**Defect 4**: Missing `"success": True` in return dict | Identified | Pending Fix |
| **JARVIS AI Tactical Insights** | `src/jarvis_service.py`, `src/jarvis_engineering_insights.py` | Session ID, Primary Driver, Reference Driver | Structured findings by category (session, pace, strategy, tyres, corner loss) | FastF1 quicklaps, sector deltas, corner time loss | **Defect 5**: Only passed 4 args to `analyze_undercut_overcut` (missing `rival_base_pace_s`)<br>**Defect 6**: Wrong case matching (`rec == 'undercut'` vs `'EXECUTE_UNDERCUT'`)<br>**Defect 7**: Checked non-existent `tyre_res.get('stints')` | Identified | Pending Fix |
| **Command Center Cockpit** | `src/command_center_service.py` | Session ID, Primary Driver, Reference Driver | Header, telemetry tower, tyre state, pace delta, strategy, race control | FastF1 session results, laps, weather, track status | **Defect 8**: `if strat.get('success')` check failed due to missing key<br>**Defect 9**: Tyre degradation key mismatch | Identified | Pending Fix |
| **ML Inference Engine** | `src/ml_service.py` | `compound`, `fuel_kg`, `track_temp` | `prediction_s_per_lap`, feature importances | RandomForest trained on session stint regressions | **Defect 10**: Overly strict `len(X) < 10` stint threshold | Identified | Pending Fix |
| **Distance-Aligned Telemetry** | `src/telemetry_analysis_service.py`, `src/time_loss_attribution.py` | FastF1 lap telemetry for primary & reference drivers | Distance-aligned traces (Speed, Throttle, Brake, Gear, DeltaTime), corner opportunities | FastF1 interpolated telemetry arrays | Validated: 1.0m grid alignment & corner detection functional | Verified | Tested |
| **Monte Carlo Race Simulator** | `src/monte_carlo_engine.py`, `src/full_field_simulator.py` | Circuit ID, Total Laps, Driver IDs, Sim Count | Stochastic finishing position distributions, win/podium probabilities, regret | Vectorized stochastic simulation with lognormal pit variance | Validated: P(sum) == 100%, seed-reproducible | Verified | Tested |
| **Circuits & Driver Standings** | `src/standings_service.py` | Season year, session ID | Schedule, circuit metadata, driver standings, points | FastF1 official event schedule and session results | Validated: Real driver standings and team colors | Verified | Tested |
| **3D Track Spatial Replay** | `src/replay_service.py`, `src/three_d_replay_engine.py` | Session ID, Frequency Hz | Downsampled 3D spatial coordinates (X, Y, Z) and timestamp arrays | FastF1 `session.pos_data` | Validated: Downsampled real coordinate stream | Verified | Tested |

---

## 2. Model Correctness & Root-Cause Remediation Plan

### Remediation A: `src/jarvis_service.py`
- Pass `r_median` as `rival_base_pace_s` to `analyze_undercut_overcut`.
- Match recommendation tactic with case-insensitive check (`"undercut"` in `rec.lower()` / `"overcut"` in `rec.lower()`).
- Correctly parse `tyre_res.get("degradation_slope_s_per_lap")` and `tyre_res.get("compound")`.
- Integrate top corner time-loss findings from `TelemetryAnalysisService.compare_laps` into JARVIS insights.

### Remediation B: `src/command_center_service.py`
- Check `if strat.get("recommended_tactic") or strat.get("success"):` so strategy panel populates.
- Read `degradation_slope_s_per_lap` for primary and reference tyres.

### Remediation C: `src/probabilistic_service.py`
- Include `"success": True` in `analyze_undercut_overcut` response payload.
- Accept dynamic `current_lap`, `total_laps`, `compound`, `tyre_age` instead of hardcoded 22/66/15.
- Supply `stints`, `optimal_pit_window`, and `projected_finish_position` in `get_canonical_strategy_state` so `OverviewPage` binds to dynamic session data without falling back to hardcoded strings.

### Remediation D: `src/unified_tyre_intelligence.py`
- Fix `fetch_session_data` unpacking from 3-tuple to dictionary extraction `data = fetch_session_data(...)` and `laps = data.get('laps', pd.DataFrame())`.

### Remediation E: `src/ml_service.py`
- Lower training data threshold from 10 stints to 4 stints, adjusting random forest estimators dynamically based on available data size.
