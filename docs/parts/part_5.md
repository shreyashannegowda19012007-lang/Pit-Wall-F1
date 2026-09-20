# PART V — MATHEMATICS AND MODELS

This section demystifies the backend engines of Pitwall F1, explaining exactly how the software calculates its probabilities, inferences, and strategy recommendations. 

## 21. Strategy Mathematics

The foundation of any race strategy is the concept of Total Race Time. The objective is simply to complete the race distance in the lowest possible time.

### The Equation of a Race
A deterministic race simulation is calculated as:
`Total Time = Sum(Base Lap Times) + Sum(Tyre Degradation per lap) + Sum(Pit Stop Time Losses)`

- **Base Lap Time:** The fundamental pace of the car and driver combination. If a car is inherently slow, no strategy will yield a win.
- **Tyre Degradation:** This is a cumulative penalty. If degradation is 0.1s per lap, Lap 1 penalty is 0.1s, Lap 2 penalty is 0.2s, Lap 3 is 0.3s. This creates an exponential decay in performance.
- **Pit Stop Time Loss:** The physical time it takes to drive down the pit lane at the speed limit (usually 80 km/h), change the tyres (approx 2.5s), and exit. In Pitwall F1, this is treated as a static penalty (e.g., 20 seconds) added to the lap time of the pit-in lap.

The Strategy Engine attempts to find the mathematical minimum of this equation by altering the number of pit stops and the laps on which they occur.

---

## 22. Race Simulation

How does Pitwall represent a race mathematically?

In the `monte_carlo_engine.py`, a race is modeled as a loop iterating over the remaining laps. The state of the simulation is defined by an array of drivers, each possessing current variables:
- `Track Position` (Distance covered)
- `Tyre Compound`
- `Tyre Age`
- `Base Pace`

For each tick of the loop (representing one lap), the engine calculates the time taken for that lap by applying the degradation slope to the base pace. It then updates the `Track Position` variable for every driver. If the updated positions result in one driver physically passing another (i.e., their distance covered exceeds the car ahead), an overtake is recorded in the simulation state.

---

## 23. Monte Carlo Method

A deterministic simulation is flawed because it assumes the degradation slope and the pit stop times will be perfectly executed. The Monte Carlo method acknowledges chaos.

### Step-by-Step Simulation Process
1. **Initialize Universe:** The engine copies the current race state.
2. **Inject Noise:** For the next lap, the engine takes the calculated lap time (e.g., 92.500s) and applies a random variance using `np.random.default_rng().normal()`. The variance might be +/- 0.3 seconds, simulating human error or minor traffic.
3. **Simulate Pit Stops:** If a driver is scheduled to pit, the engine calculates the pit loss using a Lognormal distribution. Most stops will cluster around 20 seconds, but there is a statistical tail allowing for a 28-second disaster stop.
4. **Iterate to Checkered Flag:** The loop continues until the final lap. The finishing order is recorded.
5. **Reset and Repeat:** The engine discards the universe, resets to the current actual race state, and runs the process again, generating a slightly different outcome due to the random noise.
6. **Aggregate:** After 250 parallel universes are simulated, the engine counts how many times the primary driver finished in each position. If they won 150 times, the Win Probability is 60%.

---

## 24. Tyre Degradation Mathematics

Pitwall F1 utilizes Empirical Linear Regression to model degradation.

### The Calculation
The `unified_tyre_intelligence.py` engine extracts the lap times for a driver's current stint. 
`Lap Times = [92.1, 92.2, 92.4, 94.8, 92.6]`

1. **Filtering:** The engine applies an interquartile range (IQR) filter or hard boundary limits to remove outliers. The `94.8` lap (perhaps caused by a mistake or traffic) is discarded to prevent it from skewing the data.
2. **Regression:** Using `numpy.polyfit()`, the engine calculates the line of best fit through the remaining valid data points.
3. **Slope Extraction:** The slope of this line (e.g., `0.11`) represents the degradation in seconds per lap.

### Contamination
This mathematical model can be contaminated by "Pace Management." If a driver is intentionally driving slowly to save fuel, their lap times will be artificially flat, resulting in a degradation slope near zero. The model interprets this as a "perfect" tyre, when in reality, the driver is simply coasting. The engineer must use radio context to validate the math.

---

## 25. ML Models

Pitwall F1 utilizes Machine Learning to predict events that deterministic physics cannot easily model.

### Model: Overtake Probability
- **Purpose:** To predict the likelihood of a successful overtake within the next lap.
- **Algorithm:** Random Forest Classifier (`model.pkl`).
- **Features (Inputs):** `Gap` (seconds to car ahead), `Speed Delta` (difference in top speed on the straight), and `DRS Status` (0 or 1).
- **Target (Output):** Binary (1 = Overtake Successful, 0 = Unsuccessful).
- **Inference Process:** The `production_ml_engine.py` script receives the live features from the telemetry pipeline. It executes the `.predict_proba()` method on the loaded Random Forest model. The resulting percentage (e.g., 72%) is routed to the Command Center UI.
- **Limitations:** The model is highly dependent on the historical data it was trained on. It does not account for qualitative factors such as a driver's aggressive reputation, or specific defensive lines taken on the track.

---

## 26. Reinforcement Learning

The Pitwall repository contains experimental Reinforcement Learning algorithms (`f1_strategy_env.py` and `rl_strategy_agent.py`).

### The RL Architecture
- **Purpose:** To train an autonomous AI agent to discover the optimal pit stop strategy without hardcoded heuristics.
- **Environment:** A custom Python class conforming to the OpenAI Gym standard. It simulates the race progression.
- **State:** The observation space includes the current lap, the tyre compound, tyre age, and the gaps to opponents.
- **Action:** The agent can choose to `Stay Out` (Action 0) or `Pit` (Action 1-3, selecting a specific compound).
- **Reward:** The agent receives a positive reward for finishing in a high position, and a massive negative penalty for finishing low. Over thousands of training episodes, it learns to maximize the reward by pitting at the correct crossover points.

### Production Status and Influence
**TRUTHFULNESS WARNING:** The RL agent is strictly **EXPERIMENTAL**. While the code exists and can be trained, the agent is *orphaned* from the main UI orchestration path. It does not currently influence the Monte Carlo recommendations, nor does it override the deterministic strategy engine. It should be viewed as a research module for future development, not a production decision-maker.

---

## 27. Decision Architecture

When an engineer asks a question, how does the system choose which backend engine to deploy?

- **If the question involves past/current physical reality (e.g., "Where did we lose time?"):** The system relies purely on **Deterministic Calculations** (Telemetry Performance Lab). It interpolates arrays and executes basic calculus. No simulation or AI is involved.
- **If the question involves the future of the entire race (e.g., "When should we pit?"):** The system deploys the **Monte Carlo Simulator**, relying on statistical distributions and probabilities.
- **If the question involves the immediate outcome of a complex interaction (e.g., "Will we pass him?"):** The system deploys the **Machine Learning** inference models, relying on trained historical pattern recognition.

The architecture ensures that the right mathematical tool is used for the right tactical problem.
