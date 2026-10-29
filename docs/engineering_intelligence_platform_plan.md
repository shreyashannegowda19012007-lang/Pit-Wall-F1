# Pitwall F1 Engineering Intelligence Platform — Master Plan & Execution Tracker

## System Architecture & Provenance Matrix

### Data Provenance Classifications
Every metric and channel across the platform is explicitly labeled into one of five categories:
1. **MEASURED**: Direct physical sensor readings (Speed, RPM, Throttle pedal %, Brake pressure/flag, nGear, DRS status, Air/Track Temp, Humidity, Rain flag, Lap timing).
2. **DERIVED**: Deterministic mathematical & physical derivations from measurements (Longitudinal acceleration $a_x = dv/dt$, Lateral acceleration $a_y = v^2/R$, Curvature $\kappa$, Speed deltas $\Delta v$, Distance-integrated delta time $\Delta t$, Micro-sector split times).
3. **ESTIMATED**: Statistical, regression, or probabilistic models (Tyre degradation slope $\beta$ in s/lap, fuel-corrected baseline pace, compound crossover laps, stint life forecasts).
4. **HYPOTHETICAL**: Counterfactual what-if simulations & synthetic scenarios (Theoretical ideal lap reconstruction, alternative pit stop strategies, Monte Carlo stochastic outcomes).
5. **UNAVAILABLE**: Proprietary or confidential telemetry protected by teams (Suspension potentiometer travel, damper velocities, internal tyre carcass/surface temperatures, aerodynamic downforce in Newtons, high-frequency fuel mass flow, ERS battery cell State-of-Charge).

---

## 10-Phase Implementation Roadmap

### Phase 1: Source Discovery & Data-Provenance Architecture
- [x] Centralize provider adapter metadata (`FastF1`, `OpenF1`, `Jolpica-F1`, `FIA Documents`).
- [x] Define physical units, update frequencies, API rate limits, and fallback strategies.
- [x] Formalize `DataClassification` enum and provenance headers in API responses.

### Phase 2: Unified Session & Telemetry Data Model
- [x] Canonical session format: `S-{YEAR}-{ROUND/CIRCUIT}-{SESSION_TYPE}`.
- [x] Standardized telemetry dataframe schema with strict boundary validation.
- [x] Ensure non-destructive data pipelines preserving raw timestamps and distance grids.

### Phase 3: Data Ingestion, Normalization, Validation & Caching
- [x] FastF1 Parquet / SQLite cache validation with SHA-256 manifests.
- [x] OpenF1 cache session with SQLite backend and rate-limiting exponential backoff.
- [x] Automated validation against NaN, Inf, and non-physical sensor anomalies.

### Phase 4: Driver & Vehicle-Performance Analysis
- [x] Micro-sector delta comparison.
- [x] Braking-point analysis (braking distance, entry speed, peak deceleration in $g$).
- [x] Apex cornering minimum-speed retention.
- [x] Throttle pickup delay and application gradient.
- [x] 5-phase corner decomposition (entry, braking, apex, exit, straight).
- [x] Vehicle dynamics: longitudinal $a_x$, lateral $a_y$, $g$-load calculation.
- [x] Aerodynamic efficiency proxy (high-speed straight deceleration, top speed vs DRS).
- [x] Driver consistency metrics ($\sigma$, IQR, coefficient of variation).
- [x] Theoretical ideal-lap reconstruction with explicit continuous-lap traction limitation disclaimers.

### Phase 5: Tyre & Race-Strategy Models
- [x] Compound-specific degradation rates ($\beta$ in s/lap).
- [x] Fuel-corrected stint pace evolution.
- [x] Out-lap warm-up and in-lap pit loss deltas.
- [x] Compound crossover point calculation.
- [x] Performance cliff detection.
- [x] Multi-stop strategy optimizer (1-stop, 2-stop, 3-stop options).

### Phase 6: Race Simulation & Predictive Analytics
- [x] Advanced Monte Carlo stochastic race simulator with reproducible seeds.
- [x] Safety car & VSC probability modeling based on circuit incident history.
- [x] Traffic and dirty-air lap time penalty modeling.
- [x] Finishing position probability distributions and confidence intervals.

### Phase 7: Race Operations & Historical Intelligence
- [x] Timing tower & interval array.
- [x] Pit-stop timeline with stationary time and net pit-lane loss.
- [x] Race control event timeline (flags, SC, VSC, track limits, investigations).
- [x] Team radio timeline with audio links and transcription disclaimers.
- [x] FIA Sporting & Technical regulations reference dossier.
- [x] Historical career trends and teammate head-to-head records via Jolpica Ergast.
- [x] Regulation-era comparisons (Ground Effect 2022-2024 vs Hybrid 2014-2021).

### Phase 8: Engineering Insights & JARVIS Evidence Integration
- [x] Automated post-session engineering debrief generator.
- [x] Evidence graph linking claims to driver, session, lap, corner, telemetry channel, and model version.
- [x] Explicit uncertainty labeling and recommended engineering follow-ups.

### Phase 9: Model Validation & Backtesting
- [x] Zero-future-data-leakage backtesting harness.
- [x] Model evaluation on held-out historical Grand Prix sessions (2024 Spain, 2023 Monaco).
- [x] Error metrics tracking (MAE, RMSE, $R^2$).
- [x] Calibration and model drift monitoring.

### Phase 10: Unified UI Integration & Complete Browser Verification
- [x] Unified workstation layout with dense engineering telemetry widgets.
- [x] Responsive controls, interactive Recharts graphs, and data provenance badges.
- [x] Production build (`npm run build`) and test suite (`pytest`) passing 100%.
- [x] Interactive browser subagent walkthrough verifying all features end-to-end.

