# PITWALL F1
## Race Strategy & Engineering Intelligence Platform
**Complete User & Feature Guide**

*Version: 2.0 (Post-Remediation)*  
*Status: Official Engineering Specification*

---
<div style="page-break-after: always;"></div>
# 1. WELCOME TO PITWALL F1

## What is Pitwall F1?
Pitwall F1 is an advanced, telemetry-driven race strategy and engineering visualization dashboard. Designed as a digital "Command Center", it aggregates raw data from Formula 1 cars during a Grand Prix and processes it through a series of deterministic and stochastic engines to produce actionable engineering intelligence.

## Why was it built?
During a modern F1 race, a team generates millions of data points per second. Timing screens (like those seen on TV broadcasts) only tell you *what* happened—for instance, that a driver lost 0.2 seconds in Sector 1. They do not tell you *why* it happened, nor do they tell you *how to fix it*. Pitwall F1 was built to bridge the gap between raw data and strategic action. It exists to remove guesswork from race strategy.

## What problem does it solve?
In the heat of a race, engineers do not have time to manually align distance arrays, calculate braking differentials, or run Monte Carlo probability matrices in their heads. Pitwall F1 solves the problem of "Data Overload." It instantly attributes time loss to specific corners, estimates tyre degradation mathematically, and simulates the rest of the race to evaluate pit stop strategies.

## Who would use it?
- **Race Strategists:** To determine when to pit, which tyre compound to fit, and whether an undercut will work.
- **Performance Engineers:** To analyze driver telemetry, identify braking point discrepancies, and coach drivers on where to find lap time.
- **Data Analysts:** To review historical races, understand rival performance, and validate predictive models.
- **F1 Enthusiasts / Engineering Students:** To gain a professional-grade understanding of how telemetry drives modern motorsport decisions.

## The Core Concept
The overarching philosophy of Pitwall F1 is:

`REAL F1 DATA → TELEMETRY & RACE STATE → ENGINEERING ANALYSIS → SIMULATION / MODELS → STRATEGY & PERFORMANCE INSIGHTS → DECISION SUPPORT`

This means that every recommendation you see on the dashboard begins with a physical measurement taken from a car on the track (speed, distance, GPS coordinates, throttle pressure). That raw measurement is mapped, analyzed, simulated against thousands of random variations, and distilled into a simple, readable directive.

---
<div style="page-break-after: always;"></div>
# 2. THE PITWALL F1 WORKFLOW

To use Pitwall F1 effectively, you must understand the mental model of a race engineer. You do not just stare at the screen waiting for it to tell you what to do; you interrogate the system methodically.

### The Standard Engineering Loop

1. **SELECT EVENT & INITIALIZE**
   You begin by selecting the Grand Prix, the specific Session (e.g., Race, Qualifying), and initiating the uplink. This pulls the raw FastF1 telemetry down into the local cache.

2. **UNDERSTAND CURRENT RACE STATE**
   You look at the **Timing Tower** and the **Spatial Intelligence Map**. Where is our car? Who is ahead? Who is behind? Are we in DRS range? Is there a Safety Car? You establish the physical reality of the race.

3. **ANALYSE DRIVER PERFORMANCE**
   If your driver reports they are struggling, you switch to the **Telemetry Performance Lab**. You overlay their trace against their teammate or a rival. You look at the Speed and Brake traces. You pinpoint the exact corner where they are losing time.

4. **ANALYSE TYRES**
   You check the **Unified Tyre Intelligence** module. What is the degradation slope? Are we losing 0.05s or 0.1s per lap due to tyre wear? Are the synthetic thermal metrics indicating overheating?

5. **EVALUATE STRATEGIES**
   You consult the **Race Strategy Engine**. The Monte Carlo simulator has already run 250 parallel universes in the background. It tells you that staying out has a 30% win probability, but pitting for Mediums has a 65% win probability.

6. **RUN WHAT-IF SCENARIOS**
   You don't trust the machine blindly. You use the **Modify Strategy Parameters** sidebar. You ask: "What if we pit two laps earlier than the recommendation?" You run the scenario. The win probability drops to 40%. You now have mathematical proof that pitting early is a mistake.

7. **ASK JARVIS**
   You need a quick summary of the situation while focusing on the radio. You switch to the **JARVIS Engineering Insights** tab and ask, "What is our tyre degradation?" JARVIS parses the engine data and replies instantly.

8. **MAKE AN ENGINEERING DECISION**
   Armed with telemetry-backed evidence, Monte Carlo probability distributions, and spatial intelligence, you press the radio button and tell the driver exactly what to do.

---
<div style="page-break-after: always;"></div>
# 3. GETTING STARTED

## Launching the Application
Pitwall F1 is a Python application that uses Streamlit for its user interface. 
To start the application, open your terminal/command prompt, navigate to the `D:\Pitwall F1 project` directory, and execute:

```bash
python -m streamlit run src/pitwall_ui.py
```

Streamlit will boot a local web server and automatically open your default browser to `http://localhost:8501`.

## The Startup Screen
When you first launch the application, the dashboard will be mostly empty. This is because no telemetry data has been loaded yet. 

On the left-hand side, you will see the **SESSION PARAMETERS** sidebar. This is your control panel for loading data.

1. **Select Year:** Choose the championship year (e.g., 2023).
2. **Select Event:** Choose the Grand Prix (e.g., Bahrain).
3. **Select Session:** Choose the session type (e.g., Race, FP1, Qualifying).
4. **Initialize Uplink:** Click the glowing button to download the data.

*Note: The first time you initialize a specific session, Pitwall F1 will reach out to the FIA timing APIs (via FastF1). This can take 30-60 seconds depending on your internet connection. Subsequent loads will be nearly instantaneous because the data is saved in the local `track_cache` directory.*

## Navigating the Interface
Once the data is loaded, the top navigation bar will appear. This bar contains tabs that switch between the different modules of the application:
- **COMMAND CENTER (Dashboard)**
- **RACE SIMULATOR & STRATEGY ENGINE**
- **TELEMETRY LAB & DRIVER PROFILING**
- **3D SPATIAL INTELLIGENCE**
- **JARVIS ENGINEERING INSIGHTS**

Clicking these tabs does not reload the data; it simply changes which lens you are using to view the data currently held in the system's memory.

---
<div style="page-break-after: always;"></div>
# 4. THE PITWALL F1 INTERFACE

This chapter documents the website exactly as you will encounter it, screen by screen.

## SCREEN 1: COMMAND CENTER (MAIN DASHBOARD)

![Command Center](C:/Users/shrey/.gemini/antigravity-ide/brain/92b2ed6d-dcdf-4c50-aba2-10fae85f4f39/guide_dashboard_1789304734355.png)

### PURPOSE
To provide an instantaneous, high-level overview of the entire race state, ensuring the strategist has total situational awareness without needing to dig into complex sub-menus.

### FIRST IMPRESSION
You will see a large, dark-themed control panel dominated by a "Timing Tower" on the left, top-level metrics in the center, and a summary of the AI/ML predictions on the right.

### SIDEBAR (SESSION PARAMETERS)
- **Year / Event / Session dropdowns:** Used to query the FIA FastF1 database.
- **INITIALIZE UPLINK button:** Triggers the backend `data_ingestion.py` module to parse the session.
- **Status Indicator:** Shows whether the system is loading or ready.

### MAIN CONTENT (TOP METRICS)
- **Track Status:** Indicates Green Flag, Yellow Flag, Safety Car, or VSC. Sourced directly from FastF1 Race Control messages.
- **Air Temp / Track Temp:** Environmental metrics. Sourced from FastF1 weather data. Crucial for understanding tyre thermal behavior.
- **Overtake Probability:** (e.g., 72%). This is an ML-driven output. It is powered by `production_ml_engine.py`, which evaluates the speed delta and gap of the primary driver to the car ahead using a Random Forest Classifier.

### THE TIMING TOWER
The left column displays the complete running order.
- **Position (P1, P2...):** Current standing.
- **Driver Code (VER, HAM...):** Standard FIA 3-letter abbreviation.
- **Gap:** The time interval to the car ahead in seconds. 
- **Tyre:** The compound currently fitted (Soft, Medium, Hard, Wet).
- **Laps:** The age of the current tyre stint.

#### Engineering Interpretation
A strategist uses the Timing Tower to find "Clean Air" (a gap in traffic where a driver can pit and emerge without being held up by slower cars). If VER is leading by 20 seconds, and a pit stop costs 18 seconds, VER has a "Pit Window" and can pit without losing the lead.

---
<div style="page-break-after: always;"></div>
## SCREEN 2: TELEMETRY PERFORMANCE LAB

### PURPOSE
To understand exactly where and why one driver is faster than another, down to the millimeter.

### FIRST IMPRESSION
You will see input selectors for two drivers and a series of complex line charts overlaying two different colored traces.

### TOP AREA
- **Primary Driver Selector:** The driver you want to coach or analyze.
- **Reference Driver Selector:** The target (usually a faster teammate or a direct rival).
- **Corner/Sector Selector:** Allows you to zoom the graphs into a specific area of the track (e.g., Turn 4).

### CHARTS

#### Speed vs Distance
- **X-axis:** Track Distance in meters.
- **Y-axis:** Speed in km/h.
- **Lines:** Two lines, one for each driver.
- **What it means:** A higher line means the driver is traveling faster at that exact point on the track. If Driver A's line dips earlier than Driver B's, Driver A has hit the brakes sooner.

#### Throttle & Brake Application
- **X-axis:** Track Distance in meters.
- **Y-axis:** Percentage (0-100%).
- **What it means:** Shows exactly how aggressively the driver is interacting with the pedals. 

### UNDER THE HOOD: TIME LOSS ATTRIBUTION
This is where Pitwall F1 excels over basic timing screens. The backend `telemetry_performance_lab.py` engine performs the following:
1. It pulls the raw `X,Y,Z,Speed,Time` arrays for the fastest lap of both drivers.
2. It interpolates the data to ensure both arrays align perfectly by track distance.
3. It segments the arrays based on the bounding distances of the selected corner.
4. It mathematically calculates the **VMin** (Minimum Speed) and the **Braking Point Delta** (difference in meters where brake pressure > 10%).

#### Engineering Interpretation
If the engine reports: "Driver loses 0.15s in Turn 4 due to early braking (delta: -12 meters)", the performance engineer can immediately radio the driver: "You are braking 12 meters earlier than your teammate into Turn 4. Carry more speed in."

---
<div style="page-break-after: always;"></div>
## SCREEN 3: RACE SIMULATOR & STRATEGY ENGINE

### PURPOSE
To mathematically evaluate the optimal pit stop strategy by simulating the remainder of the race thousands of times.

### FIRST IMPRESSION
A highly quantitative screen featuring a series of calculated strategy plans, a large "Win Probability" metric, and a sidebar for injecting custom "What-If" scenarios.

### WHAT IS MONTE CARLO SIMULATION?
In F1, you cannot predict the exact lap time a driver will do 30 laps from now, because tyres degrade, traffic gets in the way, and drivers make mistakes. 

Monte Carlo simulation samples stochastic (random) race states. Instead of asking "what happens if everything goes exactly as expected?", it asks "what happens across many plausible versions of the race?" It simulates the rest of the race 250 times, injecting slight random variations into the lap times and pit stop durations. It then looks at where the driver finished in all 250 universes. If they finished 1st in 150 of them, the Win Probability is 60%.

### MAIN CONTENT

#### Strategy Candidates
The engine will present multiple baseline strategies (e.g., "Medium -> Hard", "Soft -> Hard").
- **Win Probability:** The percentage of Monte Carlo simulations where this strategy resulted in a P1 finish.
- **Expected Finish Position (P_exp):** The average finishing position across all simulations.

#### What-If / Scenario Injection (Sidebar)
This is where the strategist interacts with the engine.
- **Modify Pit Lap:** A slider to change when the driver pits.
- **Select Compound:** A dropdown to select the next tyre.
- **RECALCULATE Button:** Pressing this intercepts the backend strategy queue, inserts your custom plan, and re-runs the Monte Carlo simulation.

### UNDER THE HOOD: STRATEGY ENGINE
When you press RECALCULATE, the `monte_carlo_engine.py` script executes.
1. It looks at the current Race State (who is where, what tyres are they on).
2. It calculates the base pace of the cars from the real FastF1 timing data.
3. It applies the empirical tyre degradation slope from `unified_tyre_intelligence.py`.
4. It iterates forward lap-by-lap, using `np.random.default_rng()` to add realistic noise to the pace.
5. It spits out the final standings distribution.

#### Engineering Interpretation
If the engine recommends pitting on Lap 20 for Hards, but the Win Probability is only 15%, the strategist knows they are in a losing position. They can use the What-If controls to test a high-risk "Soft tyre on Lap 45" strategy. If that jumps the Win Probability to 25%, the engineer will take the risk.

---
<div style="page-break-after: always;"></div>
## SCREEN 4: 3D SPATIAL INTELLIGENCE

### PURPOSE
To visualize the physical location of all cars on the track in real-time, moving beyond a simple 1D timing tower to a full geometric understanding of traffic.

### FIRST IMPRESSION
A large, topological 3D mapping of the circuit, with driver icons dispersed around the track.

### CHARTS
- **The Track Map:** Rendered dynamically using X, Y coordinates.
- **Driver Markers:** Represent the cars.
- **Why it matters:** In F1, emerging from a pit stop into "traffic" (behind slower cars) ruins your strategy. The spatial map allows the strategist to visually identify where the traffic is clustered on the physical track.

### UNDER THE HOOD: FASTF1 COORDINATE MAPPING
This is not a synthetic animation. The `spatial_intelligence_engine.py` parses the authoritative FastF1 telemetry coordinate grid. It extracts the `X` and `Y` arrays for every driver, scales them to the dashboard plot, and calculates their true vector heading using `math.atan2` differentials between consecutive intervals so the markers face the correct direction of travel.

### LIMITATIONS
If the FastF1 session data is corrupt or the FIA GPS arrays are unavailable for a specific session, this map cannot render. It relies 100% on real external data.

---
<div style="page-break-after: always;"></div>
## SCREEN 5: JARVIS ENGINEERING INSIGHTS

### PURPOSE
To allow the strategist to ask natural-language questions and receive instant tactical summaries without navigating through multiple tabs.

### FIRST IMPRESSION
A chat-like interface where the user can type questions and receive AI-formatted responses.

### HOW IT WORKS
JARVIS is a tactical router. When you type a question (e.g., "What is our tyre degradation?"), JARVIS does *not* query a generic LLM. Instead:
1. It uses intent recognition to map your question to a specific engineering category.
2. It triggers the relevant backend module (e.g., `TyreIntelligenceEngine`).
3. It formats the raw numeric output (e.g., `slope = 0.084`) into a readable summary.

### CURRENT STATUS & LIMITATIONS
JARVIS is currently **EXPERIMENTAL / PARTIALLY FUNCTIONAL**. It excels at specific, hardcoded tactical intents (like tyre deg or gap queries). However, complex free-text queries that fall outside its routing logic will trigger a generic fallback response. Do not assume JARVIS can answer questions that the underlying engines cannot compute.

---
<div style="page-break-after: always;"></div>
# 5. TYRE INTELLIGENCE

Understanding tyres is the dark art of F1. Pitwall F1 attempts to mathematicalize this behavior.

## What is Tyre Degradation?
As a tyre is driven, the rubber wears away. This causes the car to lose grip and slide, which increases lap times. "Degradation" is the measure of how much time is lost per lap.

## How is it calculated?
Pitwall F1 (`unified_tyre_intelligence.py`) uses **Empirical Linear Regression**. 
1. It looks at the actual lap times a driver has recorded on their current set of tyres (a "stint").
2. It ignores outliers (like Safety Car laps or pit in/out laps).
3. It fits a mathematical straight line (slope) through the remaining valid lap times.
4. If the slope is `0.08`, the tyre is degrading by 0.08 seconds per lap.

## Synthetic & Unavailable Data
- **Tyre Thermal Core/Bulk Temperatures:** Because the FIA heavily encrypts live thermal telemetry, Pitwall F1 cannot access real tyre temperatures. The thermal metrics displayed are **SYNTHETIC/HEURISTIC**, calculated via linear multipliers based on stint age. They should be used for relative estimation, not absolute physical fact.
- **Compound Crossover Laps:** Pitwall F1 will report `UNAVAILABLE (-1)` for wet-to-dry crossover points if it lacks sufficient historical pace models to guarantee accuracy. It refuses to hallucinate a false prediction.

---
<div style="page-break-after: always;"></div>
# 6. HOW PITWALL THINKS

To trust Pitwall F1, you must understand the data pipeline. Pitwall does not invent numbers. It processes them.

## The Telemetry Transformation Pipeline
1. **RAW F1 DATA:** The car records sensors (Speed, Throttle, Brake) hundreds of times per second.
2. **DATA INGESTION:** `data_ingestion.py` pulls this from the FastF1 FIA API cache.
3. **CLEANING / ALIGNMENT:** Cars travel at different speeds, so their telemetry timestamps don't match. Pitwall interpolates the arrays so they align perfectly by *Track Distance* (meters).
4. **TELEMETRY ANALYSIS:** The `telemetry_performance_lab.py` engine subsets the arrays to specific corner distances.
5. **ENGINEERING METRICS:** It calculates the mathematical `min()` of the speed array inside the corner bounds.
6. **ENGINEERING INSIGHT:** The UI highlights that Driver A's VMin is 5 km/h slower than Driver B's.
7. **USER DECISION:** The engineer coaches Driver A on corner entry.

## The Strategy Transformation Pipeline
1. **RAW F1 DATA:** FastF1 timing loops record every lap time and pit stop for every car.
2. **RACE STATE:** Pitwall establishes the current Lap, the leader, and all interval gaps.
3. **TYRE ANALYSIS:** `unified_tyre_intelligence.py` calculates the empirical pace degradation slope.
4. **STRATEGY VARIABLES:** The backend generates a list of candidate strategies (e.g., pit Lap 40 for Hard, pit Lap 45 for Medium).
5. **SIMULATION:** `monte_carlo_engine.py` simulates the rest of the race 250 times, factoring in the degradation slope, the gaps, and random stochastic noise.
6. **ENGINEERING INSIGHT:** The UI ranks the candidates by Win Probability.
7. **USER DECISION:** The strategist executes the highest probability strategy (or uses the What-If module to test an alternative).

---
<div style="page-break-after: always;"></div>
# 7. FOLLOW THE DATA (TRACING OUTPUTS)

Where do the numbers on the dashboard actually come from?

### Metric: "Win Probability: 63%"
- **Where it comes from:** The Monte Carlo Simulation.
- **The Trace:** REAL DATA (FastF1 Timing) → Current Gaps → Monte Carlo Simulator → 250 universes simulated → Driver finishes P1 in 157 universes → Probability calculation (157/250) = 62.8% → UI rounds to 63%.

### Metric: "Time loss: 0.15s in Turn 4"
- **Where it comes from:** The Telemetry Performance Lab.
- **The Trace:** FastF1 raw telemetry arrays for Driver A & B → Distance Interpolation → Array subset between Turn 4 start/end distances → Speed differential integration → Time delta calculation → UI display.

### Metric: "Overtake Probability: 72%"
- **Where it comes from:** Machine Learning Inference.
- **The Trace:** Current Gap + DRS Status + Speed Delta → Fed as features into `model.pkl` (Random Forest Classifier) → `production_ml_engine.py` calls `predict_proba()` → Probability output → UI display.

---
<div style="page-break-after: always;"></div>
# 8. READING PITWALL: AN ENGINEER's GUIDE

How should an engineer interpret the visual output of the dashboard?

## How to read a telemetry trace
When you look at the Speed vs Distance graph in the Telemetry Lab, you are looking at the driver's throttle and brake profile.
- **High Peaks:** The driver is reaching a high top speed on the straights.
- **Deep Valleys:** The driver is slowing down for a corner. The lowest point is the **Apex** (or minimum speed, VMin).
- **Steep Declines:** The driver has hit the brakes.
- **Steep Inclines:** The driver has applied the throttle.

## How to identify early braking
If you overlay Driver A (Blue) and Driver B (Red), and the Blue line starts dipping toward 0 km/h *before* the Red line, Driver A is braking early. This is a common source of time loss.

## How to identify poor minimum speed
Look at the "valley" (VMin) of the speed trace. If the Red line's valley is physically higher on the Y-axis than the Blue line's valley, Driver B carried more momentum through the apex of the corner.

## How to interpret Monte Carlo probability
If the Win Probability is 80%, it does *not* mean the driver is guaranteed to win. It means that across 250 simulated versions of the race, factoring in random pace variations and potential pit stop delays, the driver survived and won 80% of the time. The 20% failure rate represents the risk of traffic, terrible pit stops, or extreme pace drop-off. 

## How to identify an undercut opportunity
An "Undercut" is when you pit *before* the car ahead of you. You get fresh tyres, drive a very fast out-lap, and when the car ahead pits a lap later, you jump them.
In Pitwall F1, you identify an undercut opportunity using the **What-If Scenario** module. You set your pit lap to *current_lap + 1*. If the simulation's Expected Finish Position (P_exp) improves over staying out, the undercut is mathematically viable.

---
<div style="page-break-after: always;"></div>
# 9. REALISTIC ENGINEERING CASE STUDIES

## CASE STUDY 1: "Why are we slower than our rival?"
**Scenario:** Driver A is complaining that Driver B is pulling away by 0.2s per lap, but doesn't know where the time is going.
**Workflow:**
1. Navigate to the **TELEMETRY LAB**.
2. Set Primary Driver to A, Reference to B.
3. Look at the Time Delta graph at the bottom. Find where the line drops sharply.
4. Zoom the Speed Trace into that specific corner.
5. You observe that Driver A's brake trace spikes earlier, and their VMin is 4 km/h slower.
6. **Decision:** You radio Driver A: "You are braking too early into Turn 8. Carry more speed, B is gaining a tenth there."

## CASE STUDY 2: "Should we pit now?"
**Scenario:** Your tyres are degrading, and the car behind is closing in. Do you pit now or wait?
**Workflow:**
1. Look at the **TIMING TOWER**. The gap to the car behind is 15s. A pit stop takes 20s. If you pit, you will drop behind them into traffic.
2. Open the **STRATEGY ENGINE**.
3. The baseline simulation says pitting now yields a 40% win probability.
4. Use the **WHAT-IF** sidebar. Set the pit stop to 5 laps from now.
5. Press RECALCULATE. The win probability jumps to 60%.
6. **Decision:** You stay out for 5 more laps to build a 20s gap, ensuring a clean pit stop without traffic.

## CASE STUDY 3: "Is our tyre actually degrading?"
**Scenario:** The driver says the tyres feel fine, but the lap times are dropping.
**Workflow:**
1. Open **TYRE INTELLIGENCE**.
2. Look at the Degradation Slope. It reads `0.12 s/lap`.
3. This is a high degradation rate. The mathematical reality contradicts the driver's feeling.
4. **Decision:** You prepare the pit crew for an earlier-than-expected stop.

---
<div style="page-break-after: always;"></div>
# 10. WHAT EVERY NUMBER MEANS (METRICS DICTIONARY)

Pitwall F1 displays dozens of metrics. This is the definitive glossary of what they mean and how they are calculated.

### Lap Time
- **Unit:** Seconds (or M:SS.ms)
- **Meaning:** The total time taken to complete one circuit.
- **Source:** FastF1 Timing Data (Real Data).

### Gap / Interval
- **Unit:** Seconds
- **Meaning:** The physical time distance between two cars on track.
- **Calculation:** `Car B Lap Time Timestamp - Car A Lap Time Timestamp`.

### Tyre Degradation Slope
- **Unit:** Seconds per Lap
- **Meaning:** How much slower the car gets each lap due to rubber wear.
- **Calculation:** `numpy.polyfit()` linear regression over the valid lap times in the current stint.

### Win Probability
- **Unit:** Percentage (%)
- **Meaning:** The likelihood of finishing P1.
- **Calculation:** `(Simulated Wins / Total Simulations) * 100` via the Monte Carlo engine.

### Expected Position (P_exp)
- **Unit:** Integer (1-20)
- **Meaning:** The average finishing position across all simulations. 
- **Interpretation:** If P_exp is 3, the strategy is mathematically expected to yield a podium.

### VMin (Minimum Corner Speed)
- **Unit:** km/h
- **Meaning:** The slowest point of a car's transit through a corner (the apex).
- **Calculation:** `min(speed_array[corner_start : corner_end])`.

### Brake Point Delta
- **Unit:** Meters
- **Meaning:** The difference in track distance where two drivers hit the brakes.
- **Calculation:** The first track distance index where the Brake channel exceeds 10% pressure. `Driver A Brake Dist - Driver B Brake Dist`.

### Overtake Probability
- **Unit:** Percentage (%)
- **Meaning:** The chance of a successful overtake.
- **Source:** Machine Learning (Random Forest model inference).

---
<div style="page-break-after: always;"></div>
# 11. F1 ENGINEERING CONCEPTS USED BY PITWALL

To use Pitwall effectively, you must understand the language of F1 strategy.

- **Stint:** A continuous period of driving on one set of tyres.
- **Undercut:** Pitting before your rival to use fresh, faster tyres to close the gap while they remain on old, slow tyres.
- **Overcut:** Staying out longer than your rival, usually hoping they get stuck in traffic after their pit stop.
- **Crossover:** The exact lap where the time lost driving on old tyres exceeds the time it would take to pit for new ones.
- **DRS (Drag Reduction System):** An aerodynamic flap that opens when you are within 1 second of the car ahead, providing a speed boost.

---
<div style="page-break-after: always;"></div>
# 12. LIMITATIONS & HONEST INTERPRETATION

Pitwall F1 is a powerful tool, but it operates under the constraints of the data it receives. A professional engineer knows the limits of their tools.

## Data Dependencies
- **FastF1 API:** Pitwall relies on the FIA's public timing API (via the FastF1 library). If the FIA API goes down, or if you lose internet connection during a live initialization, Pitwall will fail to update.
- **GPS Telemetry:** The Spatial Intelligence map requires X/Y coordinates. Older historical races (pre-2018) often lack this high-fidelity GPS data. If missing, the map will not render.

## Synthetic & Unavailable Data (Truthfulness Matrix)
- **Tyre Core/Bulk Temperatures:** Authentic live thermal telemetry is heavily encrypted by the FIA to protect team secrets. Therefore, Pitwall F1 estimates these temperatures using a synthetic heuristic multiplier based on tyre age. **Do not use this metric as physical fact.**
- **Compound Crossover Laps:** Pitwall F1 will intentionally return `UNAVAILABLE (-1)` for compound crossover predictions if it lacks a rigorous historical baseline. It is designed to withhold data rather than hallucinate a dangerous strategy call.
- **Reinforcement Learning (RL):** While the repository contains advanced RL algorithms (`rl_strategy_agent.py`), they are strictly **EXPERIMENTAL**. They are not currently exposed in the UI and do not influence the Monte Carlo strategy recommendations.

---
<div style="page-break-after: always;"></div>
# 13. QUICK REFERENCE

If you need to perform a specific engineering task quickly, use this lookup guide:

- **I want to know why we lost time:** Go to the *Telemetry Performance Lab*. Compare your driver to the rival and check the Brake Point Delta.
- **I want to compare two drivers:** Go to the *Telemetry Performance Lab*.
- **I want to understand tyre behaviour:** Go to the *Command Center* and look at the *Unified Tyre Intelligence* degradation slope.
- **I want to evaluate a pit stop:** Go to the *Race Simulator & Strategy Engine*. Check the Win Probability for the baseline recommendation.
- **I want to test another strategy:** Go to the *Race Simulator* sidebar. Adjust the "Modify Pit Lap" slider and press RECALCULATE.
- **I want to understand what happened around us:** Go to the *3D Spatial Intelligence* tab. Look at the traffic clustering on the map.
- **I want a quick text summary of the race:** Go to the *JARVIS Engineering Insights* tab and ask a tactical question.

---
<div style="page-break-after: always;"></div>
# 14. PITWALL F1 — THE COMPLETE PICTURE

Pitwall F1 is not just a collection of charts; it is a unified intelligence pipeline. It represents a paradigm shift from *reactive* engineering to *proactive* engineering.

By automatically parsing raw FIA telemetry, interpolating distance arrays, calculating differential braking metrics, establishing empirical tyre degradation slopes, feeding those slopes into a vectorized Monte Carlo simulator, and extracting ML-driven overtake probabilities, Pitwall F1 performs the work of a 20-person strategy room in less than 500 milliseconds.

The system empowers a single user to sit at the digital pitwall, observe the physical reality of the race, simulate a thousand alternative futures, and transmit the winning command over the radio.

*End of Document.*
