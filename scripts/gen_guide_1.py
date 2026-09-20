import os
from markdown_pdf import MarkdownPdf
from markdown_pdf import Section

def write_guide():
    os.makedirs('docs/guide_assets', exist_ok=True)
    brain_dir = r"C:\Users\shrey\.gemini\antigravity-ide\brain\92b2ed6d-dcdf-4c50-aba2-10fae85f4f39"
    dashboard_img = os.path.join(brain_dir, "guide_dashboard_1789304734355.png").replace("\\", "/")
    strategy_img = os.path.join(brain_dir, "guide_strategy_1789305325047.png").replace("\\", "/")
    telemetry_img = os.path.join(brain_dir, "guide_telemetry_1789305355463.png").replace("\\", "/")
    spatial_img = os.path.join(brain_dir, "guide_spatial_1789305591964.png").replace("\\", "/")
    jarvis_img = os.path.join(brain_dir, "guide_jarvis_1789305748851.png").replace("\\", "/")

    doc = []

    # 1. COVER
    doc.append("""# PITWALL F1
## Race Strategy & Engineering Intelligence Platform
**Complete User & Feature Guide**

*Version: 2.0 (Post-Remediation)*  
*Status: Official Engineering Specification*

---
<div style="page-break-after: always;"></div>
""")

    # 2. WELCOME TO PITWALL F1
    doc.append("""# 1. WELCOME TO PITWALL F1

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
""")

    # 3. THE PITWALL F1 WORKFLOW
    doc.append("""# 2. THE PITWALL F1 WORKFLOW

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
""")

    # 4. GETTING STARTED
    doc.append("""# 3. GETTING STARTED

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
""")

    # Write chunk 1
    with open('docs/PITWALL_F1_COMPLETE_USER_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write("".join(doc))

if __name__ == '__main__':
    write_guide()
