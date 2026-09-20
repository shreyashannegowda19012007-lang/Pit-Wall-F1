import os

def append_guide():
    doc = []

    # 15. DICTIONARY OF METRICS
    doc.append("""# 10. WHAT EVERY NUMBER MEANS (METRICS DICTIONARY)

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
""")

    # 16. F1 CONCEPTS
    doc.append("""# 11. F1 ENGINEERING CONCEPTS USED BY PITWALL

To use Pitwall effectively, you must understand the language of F1 strategy.

- **Stint:** A continuous period of driving on one set of tyres.
- **Undercut:** Pitting before your rival to use fresh, faster tyres to close the gap while they remain on old, slow tyres.
- **Overcut:** Staying out longer than your rival, usually hoping they get stuck in traffic after their pit stop.
- **Crossover:** The exact lap where the time lost driving on old tyres exceeds the time it would take to pit for new ones.
- **DRS (Drag Reduction System):** An aerodynamic flap that opens when you are within 1 second of the car ahead, providing a speed boost.

---
<div style="page-break-after: always;"></div>
""")

    # 17. LIMITATIONS & TRUTHFULNESS
    doc.append("""# 12. LIMITATIONS & HONEST INTERPRETATION

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
""")

    with open('docs/PITWALL_F1_COMPLETE_USER_GUIDE.md', 'a', encoding='utf-8') as f:
        f.write("".join(doc))

if __name__ == '__main__':
    append_guide()
