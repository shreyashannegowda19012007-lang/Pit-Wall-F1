import os

def append_guide():
    doc = []

    # 11. HOW PITWALL THINKS
    doc.append("""# 6. HOW PITWALL THINKS

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
""")

    # 12. FOLLOW THE DATA
    doc.append("""# 7. FOLLOW THE DATA (TRACING OUTPUTS)

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
""")

    # 13. READING PITWALL (INTERPRETATION GUIDE)
    doc.append("""# 8. READING PITWALL: AN ENGINEER's GUIDE

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
""")

    # 14. REALISTIC ENGINEERING CASE STUDIES
    doc.append("""# 9. REALISTIC ENGINEERING CASE STUDIES

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
""")

    with open('docs/PITWALL_F1_COMPLETE_USER_GUIDE.md', 'a', encoding='utf-8') as f:
        f.write("".join(doc))

if __name__ == '__main__':
    append_guide()
