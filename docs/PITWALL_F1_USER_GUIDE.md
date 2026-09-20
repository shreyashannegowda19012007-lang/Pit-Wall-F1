# PITWALL F1
## Race Strategy & Engineering Intelligence Platform
**Complete User & Feature Guide**
*Version 1.0 (Production)*

---
## WELCOME TO PITWALL F1
Pitwall F1 is an advanced engineering dashboard built for Formula 1 race strategists, engineers, and analysts. It translates raw data into strategic foresight.

During a Grand Prix, an F1 team receives millions of data points every second. While timing screens tell you *what* happened, Pitwall F1 tells you *why* it happened and *what to do next*.

By combining live and historical FastF1 telemetry with stochastic modeling and spatial mapping, Pitwall F1 answers critical questions like: 'Where is our driver losing time to their rival?', 'What happens if we pit right now?', and 'Is the undercut viable?'

### The Engineering Pipeline
```
REAL F1 DATA (FastF1)
        ↓
TELEMETRY & RACE STATE
        ↓
ENGINEERING ANALYSIS (Driver pace, tyre wear, corner deltas)
        ↓
SIMULATION / MODELS (Monte Carlo Stochastic Engine)
        ↓
STRATEGY & PERFORMANCE INSIGHTS (Win Probability, Recommended Pit Laps)
        ↓
DECISION SUPPORT (Actionable Engineering Directives)
```
---
## THE PITWALL F1 WORKFLOW
Pitwall F1 is designed to support the natural decision-making loop of a race engineer:

1. **SELECT EVENT:** Start by loading a Grand Prix from the archive or a Live Session.
2. **UNDERSTAND CURRENT RACE STATE:** Observe the Timing Tower and Spatial Intelligence track map to see where everyone is.
3. **ANALYSE DRIVER PERFORMANCE:** Use the Telemetry Lab to see if the driver is hitting their braking points.
4. **COMPARE RIVALS:** Overlay a competitor's trace to find exactly which corner is costing time.
5. **EVALUATE STRATEGIES:** Use the Strategy Engine to view baseline predictions for the rest of the race.
6. **RUN WHAT-IF SCENARIOS:** Propose a new strategy (e.g., pit early for Hards) and instantly simulate 1,000 parallel race universes to see if it improves win probability.
7. **MAKE AN ENGINEERING DECISION:** Relay the command over the radio.

---
## GETTING STARTED
### Launching the Application
From your terminal, run:
`python -m streamlit run src/pitwall_ui.py`

![Dashboard Landing View](C:/Users/shrey/.gemini/antigravity-ide/brain/92b2ed6d-dcdf-4c50-aba2-10fae85f4f39/guide_dashboard_1789304734355.png)

### Connecting to a Session
On the left-hand sidebar, you will see the **SESSION PARAMETERS**.
1. Select an **Event** (e.g., Bahrain).
2. Select a **Session** (e.g., RACE).
3. Click the glowing **INITIALIZE UPLINK** button.
This instructs Pitwall F1 to download and process the FastF1 telemetry arrays for the entire grid.

---
## THE MAIN DASHBOARD & TIMING TOWER
The primary view provides an instantaneous overview of the race state.

### The Timing Tower
- **What it shows:** The current running order of all 20 cars, with interval gaps.
- **Why it matters:** It is the foundation of race tracking. You must know your track position before making strategic calls.
- **Where the number comes from:** It is parsed directly from FastF1 timing data.

## TELEMETRY PERFORMANCE LAB & DRIVER COMPARISON
Formula 1 is won in the margins. The Telemetry Lab allows you to dissect a driver's lap meter by meter.

![Telemetry Lab View](C:/Users/shrey/.gemini/antigravity-ide/brain/92b2ed6d-dcdf-4c50-aba2-10fae85f4f39/guide_telemetry_1789305355463.png)

### How to use it
1. Navigate to the **TELEMETRY LAB** tab.
2. Select your Primary Driver and a Reference Driver.
3. The graphs overlay Speed (km/h), Throttle %, and Brake application against Track Distance (m).

### What to look for
Look for areas where the two lines diverge. For example, if Driver A's speed line drops sooner than Driver B's, Driver A is braking earlier.

### Under the hood: Time Loss Attribution
Pitwall doesn't just show you lines; it does the math. The backend `telemetry_performance_lab.py` engine pulls the raw FastF1 arrays for both drivers, aligns them by distance, isolates specific corner boundaries (e.g., Turn 1), and calculates physical deltas (e.g., `Speed_DriverA.min() - Speed_DriverB.min()`). If a driver is losing 0.15s, Pitwall tells you exactly which corner caused it.

---
## CIRCUIT / SPATIAL INTELLIGENCE
![Spatial Intelligence View](C:/Users/shrey/.gemini/antigravity-ide/brain/92b2ed6d-dcdf-4c50-aba2-10fae85f4f39/guide_spatial_1789305591964.png)

### What it represents
This tab renders a 3D topological map of the circuit, plotting the location of all 20 drivers dynamically.

### How Pitwall calculates it
This is powered by true telemetry, not synthetic animation. Pitwall extracts the raw `X, Y, Z` positional arrays from FastF1 for every driver at a specific timestamp. It calculates their directional heading using `math.atan2` differentials between consecutive coordinates to rotate the car icons correctly on the track map.

---
## TYRE INTELLIGENCE
### Understanding Degradation
As tyres wear out, lap times increase. This increase is called 'degradation'.
- **How Pitwall works it out:** Pitwall F1's `unified_tyre_intelligence.py` engine plots the lap times of a driver's current stint and calculates a linear regression slope. If the slope is 0.08, the driver is losing 0.08 seconds per lap to tyre wear.
- **Limitations:** Some advanced thermal metrics (Core/Bulk temperatures) are currently *heuristic* (synthetic estimates based on age multipliers) rather than direct thermal telemetry, which is heavily encrypted by the FIA.

---
## RACE STRATEGY ENGINE & MONTE CARLO SIMULATION
![Strategy Engine View](C:/Users/shrey/.gemini/antigravity-ide/brain/92b2ed6d-dcdf-4c50-aba2-10fae85f4f39/guide_strategy_1789305325047.png)

Pitwall F1 can evaluate a strategy thousands of times under slightly different race conditions. Instead of asking 'what happens if everything goes exactly as expected?', it asks 'what happens across many plausible versions of the race?'

### What is simulated?
The Monte Carlo engine (`monte_carlo_engine.py`) takes the remaining laps and generates a matrix of random noise. It uses Normal distributions for standard lap pace and Lognormal distributions for pitstop durations (since pitstops can go horribly wrong, creating a skewed distribution).

### Under the hood
The simulator evaluates the grid dynamically, measuring true lap-time deltas against opponents from the real telemetry stream. It aggregates the results of 250 parallel universes to produce a 'Win Probability' and an 'Expected Finish Position'.

---
## WHAT-IF SCENARIO ANALYSIS
You don't just have to accept the default recommendation. The **Modify Strategy Parameters** panel allows you to intervene.

### User Workflow
1. Open the sidebar slider: 'What if we pit on Lap 45 instead of 40?'
2. Change the compound to 'SOFT'.
3. Click **RECALCULATE**.
4. Pitwall intercepts the strategy queue, injects your new parameters, and re-runs the Monte Carlo simulation. If the Win Probability goes up, you should consider taking the risk.

---
## JARVIS — THE ENGINEERING ASSISTANT
![Jarvis View](C:/Users/shrey/.gemini/antigravity-ide/brain/92b2ed6d-dcdf-4c50-aba2-10fae85f4f39/guide_jarvis_1789305748851.png)

JARVIS is a tactical AI assistant designed to answer natural language queries.

### How it works
JARVIS uses intent routing (via regex/heuristics) to map your question to internal engine functions.
- **USER:** 'What is our tyre degradation?'
- **JARVIS:** Routes to `TyreIntelligenceEngine`, extracts the empirical slope, and answers: 'Degradation is 0.084s per lap.'
- **STATUS:** JARVIS is currently classified as *Partially Functional / Experimental*. Complex free-text queries outside of predefined tactical intents will fall back to generic responses.

---
## MACHINE LEARNING INTELLIGENCE
### Overtake Probability Model
- **What it does:** It predicts the percentage chance that a driver will successfully overtake the car ahead.
- **How it works:** A Random Forest Classifier (`model.pkl`) evaluates the current Gap (seconds), DRS Status, and Speed Delta between the two cars. The backend script `production_ml_engine.py` runs `predict_proba` to generate the percentage you see on the dashboard.

---
## REINFORCEMENT LEARNING (EXPERIMENTAL)
The repository contains advanced Reinforcement Learning environments (`f1_strategy_env.py`) where an AI agent attempts to learn optimal pitstop laps via reward maximization. 

**Current Status:** Experimental/Orphaned. The RL agent is not currently exposed in the UI or active in production decision-making.

---
## REAL DATA VS CALCULATED DATA VS MODEL OUTPUT
It is critical for a race engineer to know the provenance of their data:

- **REAL DATA:** Lap times, Telemetry (Speed/Brake), and Track Positions come directly from the FIA via FastF1.
- **CALCULATED METRICS:** Tyre degradation slopes and corner time-loss deltas are mathematically derived from Real Data.
- **SIMULATION:** Win Probabilities are statistical outcomes from the Monte Carlo engine.
- **ML OUTPUT:** Overtake chances are inferences from a trained Random Forest model.
- **SYNTHETIC DATA:** Tyre Core Thermal temperatures are currently heuristic multipliers due to encrypted real-world sensors.

---
## FEATURE LIMITATIONS & DATA REQUIREMENTS
- **Spatial GPS Accuracy (DATA DEPENDENT):** Requires FastF1 telemetry arrays. If the session lacks X/Y arrays, the track map cannot render.
- **Tyre Crossover Laps (UNAVAILABLE):** Explicitly disabled to prevent hallucinating strategy calls when insufficient historical wet/dry pace models exist.
- **Live Mode (LIMITED):** Fully dependent on the stability of the external FastF1 / SignalR live timing stream.

---
## PITWALL F1 IN ONE PAGE
**WHAT PITWALL F1 IS:** A professional Command Center dashboard for F1 engineering.

**WHAT DATA IT USES:** Real-time and archived FastF1 telemetry and timing data.

**WHAT IT ANALYSES:** Driver braking points, corner speeds, and tyre degradation slopes.

**WHAT IT SIMULATES:** Thousands of parallel race universes via Monte Carlo to determine the safest and fastest pitstop strategy.

**WHO SHOULD USE IT:** Race Strategists, Performance Engineers, and Data Analysts.

**HOW EVERYTHING CONNECTS:** Raw Telemetry feeds the Performance Lab (driver coaching) and the Tyre Intelligence module (degradation), which feeds the Strategy Engine (pit options), which feeds the Monte Carlo simulator (outcome testing), presenting a final, actionable Recommendation on the UI Dashboard.

