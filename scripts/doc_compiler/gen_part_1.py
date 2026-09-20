import os

def generate():
    content = """# PART I — UNDERSTANDING PITWALL F1

## 1. Introduction

### What Pitwall F1 Is
Pitwall F1 is an advanced, telemetry-driven race strategy and engineering intelligence platform built for Formula 1. It is a comprehensive digital "Command Center" designed to aggregate high-fidelity raw telemetry data, calculate physical performance metrics, simulate race outcomes using stochastic mathematical models, and present actionable engineering directives. Rather than functioning as a passive dashboard that merely displays numbers, Pitwall F1 is an active analytical engine. It ingests spatial coordinates, lap times, speed traces, and tyre degradation slopes, and transforms them into strategic foresight.

### The Problem It Solves
During a modern Formula 1 Grand Prix, a race team is inundated with millions of data points every second. While traditional timing screens—such as those seen on television broadcasts—tell an engineer *what* has happened (for example, that a driver lost 0.2 seconds in Sector 1), they fail to explain *why* it happened or *how to rectify it*. 

In the high-pressure environment of the pitwall, engineers do not have the luxury of time. They cannot manually download CSV files, align distance arrays in Excel, calculate braking differentials, and run Monte Carlo probability matrices in their heads before the driver reaches the pit entry. Pitwall F1 solves the problem of "Data Overload" and "Analytical Latency." It instantly attributes time loss to specific corners, estimates tyre degradation mathematically, and simulates the rest of the race thousands of times to evaluate pit stop strategies, delivering the answer before the car completes the lap.

### Intended Users
The platform is designed to be used by the core tactical team during a race weekend, or during post-race debriefs:
- **Race Strategists:** Professionals responsible for determining when a driver should pit, which tyre compound should be fitted, and whether aggressive tactical maneuvers like an undercut or overcut are mathematically viable.
- **Performance Engineers:** Engineers focused on the physical driving of the car. They use the platform to analyze driver telemetry, identify braking point discrepancies, and coach drivers on where to find lap time.
- **Data Scientists & Analysts:** Personnel responsible for reviewing historical races, understanding rival performance envelopes, and validating predictive machine learning models.
- **F1 Enthusiasts & Engineering Students:** Individuals seeking a professional-grade understanding of how raw telemetry drives modern motorsport decisions, moving beyond basic fan engagement into applied mathematics.

### Engineering Philosophy
The foundational philosophy of Pitwall F1 is the absolute separation of measured reality from simulated probability. The system is built on the premise that an engineering decision is only as good as the provenance of the data supporting it. Therefore, Pitwall F1 rigorously separates direct physical measurements (like speed and track position) from derived metrics (like corner time-loss) and simulated outcomes (like win probability). The user is always aware of whether they are looking at a hard fact, a mathematical calculation, or a statistical projection.

### What Makes It Different From a Conventional Dashboard
A conventional dashboard is essentially a spreadsheet with a graphical user interface; it plots whatever data it receives. Pitwall F1 is a calculation engine first, and a dashboard second. When you look at the Telemetry Performance Lab, the application has actively interpolated two different drivers' telemetry arrays to force them to align perfectly by track distance, mathematically bounded the data to a specific corner, and integrated the speed differential to output a time-loss value. The dashboard simply renders the result of this complex backend operation.

### What Questions Pitwall Is Designed to Answer
Pitwall F1 is built to answer the fundamental questions heard on team radios every weekend:
- "Why are we slower than our rival?"
- "Where are we losing time?"
- "Are we braking too early?"
- "Is the tyre actually degrading, or is the driver just managing pace?"
- "Should we pit now, or extend the stint?"
- "What happens if a Safety Car is deployed right now?"
- "What is the probability that an overtake will be successful?"

### What It Is NOT Designed to Replace
Pitwall F1 is a decision support tool, not an autonomous race director. It is not designed to replace the intuition, experience, and context-awareness of a human race engineer. For example, while the Monte Carlo engine can calculate that pitting for Hard tyres yields a 60% win probability, it cannot account for a driver reporting over the radio that the track surface is feeling unexpectedly slippery, or that rain is visible on the horizon but not yet hitting the weather sensors. The system provides the mathematical baseline; the human makes the final call.

---

## 2. The Pitwall F1 Workflow

Understanding Pitwall F1 requires understanding the mental model of a race engineer. The application is not meant to be read linearly from left to right. Instead, it is designed to support a cyclical, iterative workflow that repeats constantly throughout a session.

### Complete Workflow From Startup
When an engineer boots up Pitwall F1, they are looking at a blank slate. The system must first be populated with the physical reality of the event.

**1. Selecting a Session and Loading Data**
The workflow begins in the Session Parameters sidebar. The user selects the Year, the Event (e.g., Bahrain Grand Prix), and the Session (e.g., Race or Qualifying). Upon initializing the uplink, Pitwall F1 reaches out to the FastF1 data cache. It downloads the complete timing data, the high-frequency telemetry arrays (speed, throttle, brake, RPM, gear, DRS), the spatial GPS coordinates, and the weather data for all 20 cars.

**2. Exploring the Race State**
With the data loaded, the engineer's first task is to establish situational awareness. They look at the Command Center. The Timing Tower provides the absolute truth of the current running order, the time intervals between cars, and the age of the tyres fitted to each car. The engineer now knows exactly where their car is relative to the competition.

**3. Selecting a Driver and a Comparison Driver**
To move from general awareness to specific analysis, the engineer selects their Primary Driver (the car they are responsible for) and a Reference Driver (usually a teammate or a direct rival ahead on track). 

**4. Analysing Telemetry**
If the Primary Driver is losing 0.2 seconds per lap to the Reference Driver, the engineer navigates to the Telemetry Performance Lab. They overlay the two drivers' traces. They look specifically at the braking zones. If the Primary Driver's speed trace dips earlier than the Reference Driver's, they have identified the source of the time loss: early braking.

**5. Evaluating Tyres**
Next, the engineer must understand the physical state of the car. They move to the Unified Tyre Intelligence module. The system has calculated the empirical degradation slope of the current tyre stint. If the degradation is high (e.g., 0.15 seconds of pace lost per lap), the tyres are failing and a pit stop is imminent.

**6. Evaluating Strategy and Running Simulations**
Knowing that a pit stop is required, the engineer consults the Race Strategy Engine. The Monte Carlo simulator has already run 250 parallel universes based on the current race state and tyre degradation. It presents a baseline strategy recommendation, such as pitting on Lap 40 for Hard tyres, and assigns it a Win Probability (e.g., 45%).

**7. Investigating Alternatives (What-If Analysis)**
A 45% win probability is risky. The engineer wonders if pitting earlier would be better. They use the What-If scenario controls. They instruct the engine to simulate a pit stop on Lap 35 for Medium tyres. They press recalculate. The Monte Carlo engine intercepts the strategy queue, injects the new parameters, and re-runs the 250 simulations. The new Win Probability is 65%. 

**8. Asking JARVIS**
While analyzing the strategy, the engineer needs to quickly confirm the gap to the car behind without losing focus on the charts. They switch to the JARVIS Engineering Assistant tab and type, "What is the gap to the car behind?" JARVIS parses the backend timing data and provides an instant text summary.

**9. Reviewing Replay**
If the engineer needs to understand how a specific event unfolded (e.g., how they lost a position during the pit stop phase), they can use the Historical Replay controls to rewind the session, watching the spatial map and timing tower reconstruct the exact moment the time was lost.

**10. Drawing an Engineering Conclusion**
Armed with the telemetry proof that the driver is braking too early, the mathematical proof that the tyres are degrading, and the simulated proof that pitting on Lap 35 yields the highest win probability, the engineer depresses the radio button and communicates the strategy to the driver. The loop is complete, and immediately begins again for the next phase of the race.

---

## 3. Getting Started

### Starting the Application
Pitwall F1 is a Python-based application that utilizes Streamlit for its frontend user interface and backend orchestration. To start the application, the user must open a terminal or command prompt, navigate to the root directory of the Pitwall F1 project, and execute the following command:

```bash
python -m streamlit run src/pitwall_ui.py
```

Streamlit will initialize the local web server and automatically open the default web browser to `http://localhost:8501`. 

### Understanding the Landing Screen
Upon launch, the user is presented with the Pitwall F1 Command Center. However, the main panels, charts, and spatial maps will be empty or displaying placeholder zeros. This is the expected behavior. Pitwall F1 is an analytical engine; it requires a dataset to process. Until a session is explicitly loaded, the engine remains idle to conserve memory and processing power.

The most critical area of the landing screen is the **SESSION PARAMETERS** sidebar on the left. This is the gateway to the data ingestion pipeline.

### Selecting Historical Sessions
To populate the dashboard, the user must instruct the system which event to analyze.
1. **Year:** The user selects the championship year (e.g., 2023). This tells the FastF1 API which historical database to query.
2. **Event:** The user selects the specific Grand Prix (e.g., Bahrain). 
3. **Session:** The user selects the session type. A Grand Prix weekend consists of Practice sessions (FP1, FP2, FP3), Qualifying, and the Race. For strategy and tyre degradation analysis, the 'Race' session is typically required, as it provides continuous long-run data.

Once the parameters are set, the user clicks the glowing **INITIALIZE UPLINK** button.

### Understanding Loading States
When the uplink is initialized, the system enters a loading state. Streamlit will display a spinner, and status messages will appear. Under the hood, the `data_ingestion.py` module is executing. 
- It first checks the local `track_cache` directory to see if the session data has been previously downloaded. 
- If it has not, it reaches out to the FIA's Ergast and SignalR timing APIs to download the raw telemetry. This process can take anywhere from 30 to 90 seconds, as it involves downloading megabytes of high-frequency sensor data for all 20 cars. 
- Once downloaded, the data is cached locally, making subsequent loads of the same session nearly instantaneous.

### What Happens When Data Is Unavailable
F1 data availability can be inconsistent, particularly for older historical seasons (pre-2018) or lower-tier sessions. If the user attempts to load a session that lacks GPS coordinate arrays or high-frequency speed telemetry, the ingestion pipeline will catch the error. The UI will display a warning indicating that the session is partially degraded. In these cases, features that rely on that specific data—such as the 3D Spatial Intelligence map—will gracefully fail and display an "Unavailable" message, rather than crashing the application or presenting fabricated data.

### What a Valid Session Looks Like
Once the uplink is successful, the dashboard bursts into life. The Timing Tower populates with the names of the drivers, their current positions, and their gaps. The top metrics display the track temperature and race status. The 3D map renders the circuit layout and places the driver markers. The Monte Carlo engine begins its initial background calculations. The system is now fully armed and ready for the engineer's first query.

### Recommended First Workflow
For a new user, the recommended first action is to simply observe the Command Center. Look at the Timing Tower and identify the race leader. Note the gap to the car in second place. Then, navigate to the Telemetry Performance Lab, set the leader as the Primary Driver, and the second-place car as the Reference Driver. Overlay their speed traces. This simple action immediately demonstrates the core power of Pitwall F1: transforming a simple time gap into a physical, visual explanation of performance.
"""
    os.makedirs('docs/parts', exist_ok=True)
    with open('docs/parts/part_1.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Part 1 written successfully.")

if __name__ == '__main__':
    generate()
