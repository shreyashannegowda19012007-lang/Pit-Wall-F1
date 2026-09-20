import os
from markdown_pdf import MarkdownPdf
from markdown_pdf import Section

def write_user_guide():
    doc = []
    
    # Paths to the screenshots captured by the subagent
    brain_dir = r"C:\Users\shrey\.gemini\antigravity-ide\brain\92b2ed6d-dcdf-4c50-aba2-10fae85f4f39"
    dashboard_img = os.path.join(brain_dir, "guide_dashboard_1789304734355.png").replace("\\", "/")
    strategy_img = os.path.join(brain_dir, "guide_strategy_1789305325047.png").replace("\\", "/")
    telemetry_img = os.path.join(brain_dir, "guide_telemetry_1789305355463.png").replace("\\", "/")
    spatial_img = os.path.join(brain_dir, "guide_spatial_1789305591964.png").replace("\\", "/")
    jarvis_img = os.path.join(brain_dir, "guide_jarvis_1789305748851.png").replace("\\", "/")
    
    # 1. Cover
    doc.append("# PITWALL F1\n")
    doc.append("## Race Strategy & Engineering Intelligence Platform\n")
    doc.append("**Complete User & Feature Guide**\n")
    doc.append("*Version 1.0 (Production)*\n\n")
    doc.append("---\n")
    
    # 2. Welcome to Pitwall F1
    doc.append("## WELCOME TO PITWALL F1\n")
    doc.append("Pitwall F1 is an advanced engineering dashboard built for Formula 1 race strategists, engineers, and analysts. It translates raw data into strategic foresight.\n\n")
    doc.append("During a Grand Prix, an F1 team receives millions of data points every second. While timing screens tell you *what* happened, Pitwall F1 tells you *why* it happened and *what to do next*.\n\n")
    doc.append("By combining live and historical FastF1 telemetry with stochastic modeling and spatial mapping, Pitwall F1 answers critical questions like: 'Where is our driver losing time to their rival?', 'What happens if we pit right now?', and 'Is the undercut viable?'\n\n")
    doc.append("### The Engineering Pipeline\n")
    doc.append("```\n")
    doc.append("REAL F1 DATA (FastF1)\n")
    doc.append("        ↓\n")
    doc.append("TELEMETRY & RACE STATE\n")
    doc.append("        ↓\n")
    doc.append("ENGINEERING ANALYSIS (Driver pace, tyre wear, corner deltas)\n")
    doc.append("        ↓\n")
    doc.append("SIMULATION / MODELS (Monte Carlo Stochastic Engine)\n")
    doc.append("        ↓\n")
    doc.append("STRATEGY & PERFORMANCE INSIGHTS (Win Probability, Recommended Pit Laps)\n")
    doc.append("        ↓\n")
    doc.append("DECISION SUPPORT (Actionable Engineering Directives)\n")
    doc.append("```\n")
    doc.append("---\n")
    
    # 3. Workflow
    doc.append("## THE PITWALL F1 WORKFLOW\n")
    doc.append("Pitwall F1 is designed to support the natural decision-making loop of a race engineer:\n\n")
    doc.append("1. **SELECT EVENT:** Start by loading a Grand Prix from the archive or a Live Session.\n")
    doc.append("2. **UNDERSTAND CURRENT RACE STATE:** Observe the Timing Tower and Spatial Intelligence track map to see where everyone is.\n")
    doc.append("3. **ANALYSE DRIVER PERFORMANCE:** Use the Telemetry Lab to see if the driver is hitting their braking points.\n")
    doc.append("4. **COMPARE RIVALS:** Overlay a competitor's trace to find exactly which corner is costing time.\n")
    doc.append("5. **EVALUATE STRATEGIES:** Use the Strategy Engine to view baseline predictions for the rest of the race.\n")
    doc.append("6. **RUN WHAT-IF SCENARIOS:** Propose a new strategy (e.g., pit early for Hards) and instantly simulate 1,000 parallel race universes to see if it improves win probability.\n")
    doc.append("7. **MAKE AN ENGINEERING DECISION:** Relay the command over the radio.\n\n")
    doc.append("---\n")
    
    # 4. Getting Started
    doc.append("## GETTING STARTED\n")
    doc.append("### Launching the Application\n")
    doc.append("From your terminal, run:\n")
    doc.append("`python -m streamlit run src/pitwall_ui.py`\n\n")
    doc.append(f"![Dashboard Landing View]({dashboard_img})\n\n")
    doc.append("### Connecting to a Session\n")
    doc.append("On the left-hand sidebar, you will see the **SESSION PARAMETERS**.\n")
    doc.append("1. Select an **Event** (e.g., Bahrain).\n")
    doc.append("2. Select a **Session** (e.g., RACE).\n")
    doc.append("3. Click the glowing **INITIALIZE UPLINK** button.\n")
    doc.append("This instructs Pitwall F1 to download and process the FastF1 telemetry arrays for the entire grid.\n\n")
    doc.append("---\n")
    
    # 5. Main Dashboard
    doc.append("## THE MAIN DASHBOARD & TIMING TOWER\n")
    doc.append("The primary view provides an instantaneous overview of the race state.\n\n")
    doc.append("### The Timing Tower\n")
    doc.append("- **What it shows:** The current running order of all 20 cars, with interval gaps.\n")
    doc.append("- **Why it matters:** It is the foundation of race tracking. You must know your track position before making strategic calls.\n")
    doc.append("- **Where the number comes from:** It is parsed directly from FastF1 timing data.\n\n")
    
    # 6 & 7. Driver Comparison and Telemetry
    doc.append("## TELEMETRY PERFORMANCE LAB & DRIVER COMPARISON\n")
    doc.append("Formula 1 is won in the margins. The Telemetry Lab allows you to dissect a driver's lap meter by meter.\n\n")
    doc.append(f"![Telemetry Lab View]({telemetry_img})\n\n")
    doc.append("### How to use it\n")
    doc.append("1. Navigate to the **TELEMETRY LAB** tab.\n")
    doc.append("2. Select your Primary Driver and a Reference Driver.\n")
    doc.append("3. The graphs overlay Speed (km/h), Throttle %, and Brake application against Track Distance (m).\n\n")
    doc.append("### What to look for\n")
    doc.append("Look for areas where the two lines diverge. For example, if Driver A's speed line drops sooner than Driver B's, Driver A is braking earlier.\n\n")
    doc.append("### Under the hood: Time Loss Attribution\n")
    doc.append("Pitwall doesn't just show you lines; it does the math. The backend `telemetry_performance_lab.py` engine pulls the raw FastF1 arrays for both drivers, aligns them by distance, isolates specific corner boundaries (e.g., Turn 1), and calculates physical deltas (e.g., `Speed_DriverA.min() - Speed_DriverB.min()`). If a driver is losing 0.15s, Pitwall tells you exactly which corner caused it.\n\n")
    doc.append("---\n")
    
    # 8. Spatial Intelligence
    doc.append("## CIRCUIT / SPATIAL INTELLIGENCE\n")
    doc.append(f"![Spatial Intelligence View]({spatial_img})\n\n")
    doc.append("### What it represents\n")
    doc.append("This tab renders a 3D topological map of the circuit, plotting the location of all 20 drivers dynamically.\n\n")
    doc.append("### How Pitwall calculates it\n")
    doc.append("This is powered by true telemetry, not synthetic animation. Pitwall extracts the raw `X, Y, Z` positional arrays from FastF1 for every driver at a specific timestamp. It calculates their directional heading using `math.atan2` differentials between consecutive coordinates to rotate the car icons correctly on the track map.\n\n")
    doc.append("---\n")
    
    # 10. Tyre Intelligence
    doc.append("## TYRE INTELLIGENCE\n")
    doc.append("### Understanding Degradation\n")
    doc.append("As tyres wear out, lap times increase. This increase is called 'degradation'.\n")
    doc.append("- **How Pitwall works it out:** Pitwall F1's `unified_tyre_intelligence.py` engine plots the lap times of a driver's current stint and calculates a linear regression slope. If the slope is 0.08, the driver is losing 0.08 seconds per lap to tyre wear.\n")
    doc.append("- **Limitations:** Some advanced thermal metrics (Core/Bulk temperatures) are currently *heuristic* (synthetic estimates based on age multipliers) rather than direct thermal telemetry, which is heavily encrypted by the FIA.\n\n")
    doc.append("---\n")
    
    # 11 & 12. Strategy & Monte Carlo
    doc.append("## RACE STRATEGY ENGINE & MONTE CARLO SIMULATION\n")
    doc.append(f"![Strategy Engine View]({strategy_img})\n\n")
    doc.append("Pitwall F1 can evaluate a strategy thousands of times under slightly different race conditions. Instead of asking 'what happens if everything goes exactly as expected?', it asks 'what happens across many plausible versions of the race?'\n\n")
    doc.append("### What is simulated?\n")
    doc.append("The Monte Carlo engine (`monte_carlo_engine.py`) takes the remaining laps and generates a matrix of random noise. It uses Normal distributions for standard lap pace and Lognormal distributions for pitstop durations (since pitstops can go horribly wrong, creating a skewed distribution).\n\n")
    doc.append("### Under the hood\n")
    doc.append("The simulator evaluates the grid dynamically, measuring true lap-time deltas against opponents from the real telemetry stream. It aggregates the results of 250 parallel universes to produce a 'Win Probability' and an 'Expected Finish Position'.\n\n")
    doc.append("---\n")
    
    # 14. What-If Analysis
    doc.append("## WHAT-IF SCENARIO ANALYSIS\n")
    doc.append("You don't just have to accept the default recommendation. The **Modify Strategy Parameters** panel allows you to intervene.\n\n")
    doc.append("### User Workflow\n")
    doc.append("1. Open the sidebar slider: 'What if we pit on Lap 45 instead of 40?'\n")
    doc.append("2. Change the compound to 'SOFT'.\n")
    doc.append("3. Click **RECALCULATE**.\n")
    doc.append("4. Pitwall intercepts the strategy queue, injects your new parameters, and re-runs the Monte Carlo simulation. If the Win Probability goes up, you should consider taking the risk.\n\n")
    doc.append("---\n")
    
    # 16. JARVIS
    doc.append("## JARVIS — THE ENGINEERING ASSISTANT\n")
    doc.append(f"![Jarvis View]({jarvis_img})\n\n")
    doc.append("JARVIS is a tactical AI assistant designed to answer natural language queries.\n\n")
    doc.append("### How it works\n")
    doc.append("JARVIS uses intent routing (via regex/heuristics) to map your question to internal engine functions.\n")
    doc.append("- **USER:** 'What is our tyre degradation?'\n")
    doc.append("- **JARVIS:** Routes to `TyreIntelligenceEngine`, extracts the empirical slope, and answers: 'Degradation is 0.084s per lap.'\n")
    doc.append("- **STATUS:** JARVIS is currently classified as *Partially Functional / Experimental*. Complex free-text queries outside of predefined tactical intents will fall back to generic responses.\n\n")
    doc.append("---\n")
    
    # 19. Machine Learning
    doc.append("## MACHINE LEARNING INTELLIGENCE\n")
    doc.append("### Overtake Probability Model\n")
    doc.append("- **What it does:** It predicts the percentage chance that a driver will successfully overtake the car ahead.\n")
    doc.append("- **How it works:** A Random Forest Classifier (`model.pkl`) evaluates the current Gap (seconds), DRS Status, and Speed Delta between the two cars. The backend script `production_ml_engine.py` runs `predict_proba` to generate the percentage you see on the dashboard.\n\n")
    doc.append("---\n")
    
    # 20. Reinforcement Learning
    doc.append("## REINFORCEMENT LEARNING (EXPERIMENTAL)\n")
    doc.append("The repository contains advanced Reinforcement Learning environments (`f1_strategy_env.py`) where an AI agent attempts to learn optimal pitstop laps via reward maximization. \n\n")
    doc.append("**Current Status:** Experimental/Orphaned. The RL agent is not currently exposed in the UI or active in production decision-making.\n\n")
    doc.append("---\n")
    
    # 23. Real vs Calculated Data
    doc.append("## REAL DATA VS CALCULATED DATA VS MODEL OUTPUT\n")
    doc.append("It is critical for a race engineer to know the provenance of their data:\n\n")
    doc.append("- **REAL DATA:** Lap times, Telemetry (Speed/Brake), and Track Positions come directly from the FIA via FastF1.\n")
    doc.append("- **CALCULATED METRICS:** Tyre degradation slopes and corner time-loss deltas are mathematically derived from Real Data.\n")
    doc.append("- **SIMULATION:** Win Probabilities are statistical outcomes from the Monte Carlo engine.\n")
    doc.append("- **ML OUTPUT:** Overtake chances are inferences from a trained Random Forest model.\n")
    doc.append("- **SYNTHETIC DATA:** Tyre Core Thermal temperatures are currently heuristic multipliers due to encrypted real-world sensors.\n\n")
    doc.append("---\n")
    
    # 27. Feature Limitations
    doc.append("## FEATURE LIMITATIONS & DATA REQUIREMENTS\n")
    doc.append("- **Spatial GPS Accuracy (DATA DEPENDENT):** Requires FastF1 telemetry arrays. If the session lacks X/Y arrays, the track map cannot render.\n")
    doc.append("- **Tyre Crossover Laps (UNAVAILABLE):** Explicitly disabled to prevent hallucinating strategy calls when insufficient historical wet/dry pace models exist.\n")
    doc.append("- **Live Mode (LIMITED):** Fully dependent on the stability of the external FastF1 / SignalR live timing stream.\n\n")
    doc.append("---\n")
    
    # 29. Pitwall F1 in One Page
    doc.append("## PITWALL F1 IN ONE PAGE\n")
    doc.append("**WHAT PITWALL F1 IS:** A professional Command Center dashboard for F1 engineering.\n\n")
    doc.append("**WHAT DATA IT USES:** Real-time and archived FastF1 telemetry and timing data.\n\n")
    doc.append("**WHAT IT ANALYSES:** Driver braking points, corner speeds, and tyre degradation slopes.\n\n")
    doc.append("**WHAT IT SIMULATES:** Thousands of parallel race universes via Monte Carlo to determine the safest and fastest pitstop strategy.\n\n")
    doc.append("**WHO SHOULD USE IT:** Race Strategists, Performance Engineers, and Data Analysts.\n\n")
    doc.append("**HOW EVERYTHING CONNECTS:** Raw Telemetry feeds the Performance Lab (driver coaching) and the Tyre Intelligence module (degradation), which feeds the Strategy Engine (pit options), which feeds the Monte Carlo simulator (outcome testing), presenting a final, actionable Recommendation on the UI Dashboard.\n\n")
    
    os.makedirs('docs', exist_ok=True)
    md_path = 'docs/PITWALL_F1_USER_GUIDE.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("".join(doc))
        
    print("Markdown generated successfully.")
    
    # Generate PDF
    pdf_path = 'docs/PITWALL_F1_USER_GUIDE.pdf'
    try:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section("".join(doc)))
        pdf.save(pdf_path)
        print("PDF generated successfully.")
    except Exception as e:
        print(f"Error generating PDF: {e}")

if __name__ == '__main__':
    write_user_guide()
