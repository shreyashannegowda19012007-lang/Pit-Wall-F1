import os

def append_guide():
    doc = []

    # 7. STRATEGY ENGINE & MONTE CARLO
    doc.append("""## SCREEN 3: RACE SIMULATOR & STRATEGY ENGINE

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
""")

    # 8. SPATIAL INTELLIGENCE
    doc.append("""## SCREEN 4: 3D SPATIAL INTELLIGENCE

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
""")

    # 9. JARVIS
    doc.append("""## SCREEN 5: JARVIS ENGINEERING INSIGHTS

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
""")

    # 10. TYRE INTELLIGENCE
    doc.append("""# 5. TYRE INTELLIGENCE

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
""")

    with open('docs/PITWALL_F1_COMPLETE_USER_GUIDE.md', 'a', encoding='utf-8') as f:
        f.write("".join(doc))

if __name__ == '__main__':
    append_guide()
