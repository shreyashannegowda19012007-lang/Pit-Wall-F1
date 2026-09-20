import os

def generate():
    content = """# PART VII — READING THE OUTPUT

## 36. Metrics Dictionary

This is the definitive glossary of the numeric outputs presented on the Pitwall F1 dashboard. 

### Lap Time
- **Definition:** The total elapsed time to complete a single circuit from the start/finish line.
- **Unit:** Seconds (or MM:SS.ms format).
- **Calculation:** Direct from FastF1 timing loops. No derivation.
- **Interpretation:** The baseline performance metric.
- **Example:** `92.450` (1 minute, 32.450 seconds).

### Gap
- **Definition:** The physical time interval between a car and the car directly ahead of it on track.
- **Unit:** Seconds.
- **Calculation:** `Car B Lap Timestamp - Car A Lap Timestamp`.
- **Interpretation:** Determines vulnerability to overtakes or viability of an undercut. 

### VMin (Minimum Corner Speed)
- **Definition:** The slowest point of a car's transit through a corner (the apex).
- **Unit:** km/h.
- **Calculation:** `min(speed_array[corner_start_distance : corner_end_distance])`.
- **Interpretation:** A low VMin indicates the driver over-slowed the car, sacrificing momentum onto the following straight.

### Brake Point Delta
- **Definition:** The physical distance difference between two drivers applying the brakes.
- **Unit:** Meters.
- **Calculation:** The track distance integer where the Brake trace array first exceeds a >10% pressure threshold, subtracted from the reference driver's equivalent distance.
- **Interpretation:** A negative delta means the primary driver braked earlier. A positive delta means they braked later (deeper).

### Tyre Degradation Slope
- **Definition:** The mathematical pace penalty incurred per lap due to rubber wear.
- **Unit:** Seconds per Lap.
- **Calculation:** Empirical linear regression (`numpy.polyfit`) over the current stint's lap times, excluding traffic outliers.
- **Interpretation:** High values (e.g., >0.15) mean the tyres are failing rapidly. 

### Win Probability
- **Definition:** The statistical likelihood of a strategy resulting in a 1st place finish.
- **Unit:** Percentage (%).
- **Calculation:** `(Simulated Wins / Total Simulations) * 100` via Monte Carlo.
- **Interpretation:** A baseline confidence score for a strategy, factoring in race chaos.

### Expected Position (P_exp)
- **Definition:** The average statistical finishing position of a strategy.
- **Unit:** Integer or Float (1.0 - 20.0).
- **Calculation:** The mean finishing position across 250 parallel Monte Carlo universes.
- **Interpretation:** A more nuanced metric than Win Probability. A strategy might have a 0% Win Prob, but a P_exp of 2.1, meaning it almost guarantees a podium.

### Overtake Probability
- **Definition:** The likelihood of successfully passing the car ahead.
- **Unit:** Percentage (%).
- **Calculation:** Inference output from the Random Forest ML classifier (`model.pkl`).
- **Interpretation:** A tactical warning system for attack or defense phases.

---

## 37. Reading Charts

Visualizations in Pitwall F1 require specific literacy.

### Telemetry Traces
- **Speed (km/h) vs Distance (m):** The fundamental graph. Peaks are straights, valleys are corners. When comparing two lines, the area between the lines represents time gained or lost. If Driver A's line is physically higher on the Y-axis than Driver B's, Driver A is pulling away.
- **Throttle (0-100%):** A flat line at 100% is ideal on a straight. Jagged, oscillating lines on corner exit indicate the driver is fighting wheelspin and correcting oversteer.
- **Brake (0-100%):** In modern F1, braking is binary and violent. The line should spike vertically to 100%, and then trail off ("trail braking") as the driver turns the wheel.

### Spatial Map
- **Dot Clusters:** If three or four dots are physically touching on the map, that is a DRS train. Cars are trapped behind each other, unable to pass.
- **Pit Lane Vectors:** Cars inside the pit lane are rendered moving slower. This allows the strategist to physically watch their car race a rival down the main straight to see who will emerge ahead.

---

## 38. Reading Strategy Tables

The Strategy Engine outputs a ranked list of candidates.
- **Ranking:** Strategies are ranked strictly by Expected Position (P_exp), not by total race time.
- **Tradeoffs:** The top strategy might recommend pitting on Lap 40 for Hards. The second strategy might recommend Lap 45 for Mediums. The engineer must read the difference in Win Probability. If the difference is only 1%, the strategies are statistically tied, and the engineer must use qualitative intuition (e.g., weather) to break the tie.

---

## 39. Understanding Confidence and Uncertainty

Pitwall F1 is not an oracle; it is a probability engine.
- **Monte Carlo Uncertainty:** If a simulation is run 250 times, the results form a distribution curve. If the curve is extremely wide (high variance), it means the strategy is highly volatile and dependent on luck (e.g., hoping for a Safety Car).
- **Model Confidence:** The ML Overtake model outputs a probability. 50% means the model is entirely uncertain. Engineers should only act decisively on probabilities >75% or <25%.

---

## 40. Avoiding Misinterpretation

The most common analytical mistake is treating calculated heuristics as physical reality.
- **Mistake:** "The Tyre Intelligence module says the tyre core temperature is 115°C, so the tyre is about to explode."
- **Reality:** Pitwall F1 does not have access to live core telemetry. That 115°C is a *synthetic heuristic multiplier*. The engineer is misinterpreting an estimation as a measurement.
- **Mistake:** "The degradation slope is 0.00, the tyres are invincible."
- **Reality:** The driver is managing pace and driving slowly on purpose, flattening the lap times and tricking the linear regression model.
"""
    os.makedirs('docs/parts', exist_ok=True)
    with open('docs/parts/part_7.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Part 7 written successfully.")

if __name__ == '__main__':
    generate()
