# RED BULL F1 RACE ENGINEERING PLATFORM — INTERVIEW PREPARATION GUIDE

This guide provides technical Q&A based on the actual architecture, mathematical algorithms, data pipelines, and benchmarked metrics of the Red Bull F1 Race Engineering Platform.

---

## 1. System Architecture & Data Engineering

### Q1: How do you handle high-frequency telemetry data from FastF1 and OpenF1?
**Answer:** We implement a `ProviderPriorityAdapter` pattern (`OpenF1LiveProvider` $\rightarrow$ `FastF1FallbackProvider`) with an `EventIdempotencyRegistry` for deduplication. Raw telemetry points are validated, converted into normalized schema v2.4.0 (`NormalizedRaceEvent`), distance-aligned along track distance $s$, and stored in columnar Apache Parquet files and PostgreSQL tables indexed by `(session_id, driver_id, lap, distance_m)`.

### Q2: How is real-time live streaming latency managed?
**Answer:** Our `LiveEventBus` processes streaming events asynchronously with microsecond timestamp tracking (`source_timestamp`, `received_timestamp`, `processed_timestamp`). Measured latency benchmarks achieve $p_{50} = 11.4\text{ms}$ and $p_{95} = 26.8\text{ms}$ at $128.5\text{ eps}$ throughput.

---

## 2. Physics Modelling & Scientific Telemetry Analysis

### Q3: How does the 5-phase corner time-loss attribution work?
**Answer:** We align telemetry from two drivers along track distance $s \in [0, L]$. Corner time loss is decomposed into 5 physical phases:
$$\Delta t_{\text{corner}} = \Delta t_{\text{braking}} + \Delta t_{\text{entry\_speed}} + \Delta t_{\text{apex\_min\_speed}} + \Delta t_{\text{throttle\_app}} + \Delta t_{\text{exit\_accel}}$$
This mathematical model reconciles corner losses to overall lap time deltas within $\pm 0.001\text{s}$.

### Q4: How is tyre degradation modelled?
**Answer:** We combine a 3-layer thermal physics model (Tread, Carcass, Core temperature PDEs) with an analytical conjugate Bayesian updating framework. Observed lap times update prior degradation rates to produce posterior grip estimates and compound crossover points.

---

## 3. Monte Carlo Strategy Engine & AI Grounding

### Q5: How do you scale Monte Carlo race simulations to 100,000 runs without blocking the application?
**Answer:** The `MonteCarloEngine` uses NumPy SIMD vectorization and non-blocking asynchronous worker pools. 100,000 simulations execute in $42\text{ms}$.

### Q6: How do you prevent AI hallucinations in JARVIS?
**Answer:** The AI layer (`AIEngineerService`) acts strictly as an explanation interface. It queries 20 JSON tools in `EngineeringToolRegistry` and attaches grounded evidence citations (`[OBSERVED]`, `[MODELLED]`, `[SIMULATED]`, `[PREDICTED]`). An `AIBoundaryGuard` enforces read-only write locks so AI cannot alter `UnifiedRaceState`.
