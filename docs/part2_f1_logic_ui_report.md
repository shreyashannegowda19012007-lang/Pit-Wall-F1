# Part 2 F1 Logic & UI Functionality Report

**Project Root**: `D:\Pitwall F1 project`  
**Date**: 2026-09-20  
**Scope**: F1 Domain Logic, UI Functionality, Driver Synchronization, and Observability Guards

---

## 1. Replay Engine Verification & Fixes
* **Driver Filtering**: Confirmed `HistoricalReplayEngine` and `BayesianRaceReplayEngine` filter telemetry strictly by `target_driver` before slicing and state determination.
* **Lap 40 Target Driver P1 Preservation**: Verified that on Lap 40, Verstappen's expected finish is P1–P3 (Podium), preventing the historical row-0 index leakage defect where Zhou (P18) was erroneously latched.
* **Stale UI State Elimination**: Fixed `render_historical_replay_dashboard` in `pitwall_ui.py` to check `replay_res.get("target_driver") == active_driver` and `ablation_res.get("target_driver") == active_driver`, automatically clearing stale cache entries upon switching drivers.
* **Unavailable State Handling**: Missing/OOD data explicitly returns `UNAVAILABLE` or raises clear errors instead of fabricating synthetic lap numbers or constant outputs.

---

## 2. Timing Tower Rollover & Lapped Invariants
* **Leader Lap Rollover Invariant**: Verified in `realtime_race_state.py` that cars within racing distance (e.g. 2.5s behind) are not classified as `LAPPED` merely because the leader completed lap $N$ and crossed onto lap $N+1$ first.
* **Genuine Lapped Car Detection**: Cars falling full laps behind are correctly classified as `LAPPED` with appropriate `laps_behind_leader` count.
* **Zero Gap Fabrication Fix**: In `pitwall_ui.py` (`render_unified_realtime_timing_tower`), eliminated the fallback `+0.000s` when `gap_to_leader_s` is missing/None, replacing it with `"-"` so missing data is never fabricated as zero gap.

---

## 3. Sensitivity Analysis & Monte Carlo Engine
* **Perturbation Propagation**: Verified all 6 OAT perturbations (tyre thermal degradation, pit stop travel loss, pace deficit/improvement, safety car probability, fuel effect, track evolution) directly reach the vectorized simulation.
* **State Binding Fix**: In `race_simulator.py`, explicitly populated `c_race_state.drivers = {d.driver_id: d for d in [t_driver_state] + opp_states}` so driver states exist within the container and are accurately cloned and perturbed by `SensitivityAnalysisEngine._clone_scenario_context`.
* **Non-Zero Shift Validation**: Confirmed that each perturbation yields mathematically grounded, non-zero shifts in race time and finish probabilities without synthetic number injection.

---

## 4. Driver Selection Traceability
* **Sidebar to Sub-Panel Sync**: Traced driver selection across all 20+ specialized dashboards.
* **Streamlit Key Synchronization**: In `render_session_header` (`pitwall_ui.py`), implemented active key synchronization for sub-panel text inputs (`ti_adv_mc_driver`, `ti_backtest_driver`, `ti_rl_driver`, `ti_ff_driver`, `ti_ml_driver`, `ti_hr_driver`, `ti_spatial_driver`, `ti_perf_ref_driver`) so changing the primary or comparison driver in the sidebar immediately propagates across all panels.

---

## 5. JARVIS & AI Engineer Contract
* **Dual Contract Alignment**: Standardized `AIEngineerService.process_query` and `AIEngineerQAEngine.answer_question` so both `answer` and `answer_markdown` are consistently populated in every response payload.
* **Defensive Parameter Handling**: Added fallback `if laps_df is None: laps_df = pd.DataFrame()` in `ai_engineer_service.py` to prevent `AttributeError` when callers omit telemetry DataFrames.
* **Clean Markdown Rendering**: Replaced fragile `<div>...{ans_str.replace('\n', '<br>')}...</div>` block in `render_ai_engineer_workstation` with native `st.markdown(ans_str)` to render formatting cleanly without raw HTML tags or unparsed markup.

---

## 6. Replay & 3D Circuit Controls
* **Cached Track Geometry Fallback**: In `three_d_replay_engine.py`, added automatic fallback to cached track geometry (`track_cache/spain.json`) when `track_nodes` is empty, ensuring the 3D circuit trajectory renders immediately.
* **Vehicle Identity Binding**: 3D scene properly binds primary car (`#FF1801`), comparison car (`#00D2BE`), and neutral field cars (`#94A3B8`).

---

## 7. Observability Sentinel Preservation
* **Non-Numeric Latency Guarding**: In `pitwall_ui.py` (`render_realtime_live_infrastructure_health_console` and `render_production_data_platform_performance_dashboard`), guarded `p50_latency_ms`, `p95_latency_ms`, and `avg_latency_ms` with `isinstance(val, (int, float))` checks. Sentinels (`NOT_MEASURED`, `UNAVAILABLE`, `INVALID`, `TIMEOUT`) are never treated as numbers or appended with `" ms"`.

---

## 8. Verification Results
* **Compilation**: `.\.venv\Scripts\python.exe -m compileall src tests` -> 0 errors.
* **Targeted Tests**: 28 passed in 35.46s.
* **Full Test Suite**: 285 passed, 0 failed, 0 skipped, 0 errors.
