import os

def generate():
    brain_dir = r"C:\Users\shrey\.gemini\antigravity-ide\brain\92b2ed6d-dcdf-4c50-aba2-10fae85f4f39"
    jarvis_img = os.path.join(brain_dir, "guide_jarvis_1789305748851.png").replace("\\", "/")

    content = f"""# PART III — JARVIS

## 13. JARVIS Engineering Assistant

![JARVIS Screen]({jarvis_img})
*Figure: The JARVIS Engineering Assistant answering a tactical query.*

### What Is JARVIS?
JARVIS (Just Another Race Visualization & Intelligence System) is the tactical AI assistant built into the Pitwall F1 platform. It provides a natural-language chat interface that allows the strategist to ask direct engineering questions and receive instant, mathematically backed answers, without needing to navigate through multiple tabs or manually inspect charts.

### Why Does It Exist?
During a critical race phase (e.g., the laps immediately preceding a pit stop), an engineer's cognitive load is extreme. They are listening to the driver on the radio, listening to the team principal on the intercom, watching the TV feed, and monitoring the Timing Tower. If they suddenly need to know the exact tyre degradation slope, they do not have the time to click into the Tyre module, locate the graph, and read the axis. JARVIS exists to eliminate this "UI Friction" by acting as a conversational bridge to the backend calculation engines.

### How Queries Work (The Routing Pipeline)
It is vital to understand that JARVIS is **not** a generic Large Language Model (LLM) connected to the internet, nor does it hallucinate answers. It is a highly deterministic intent-router.
1. **Input:** The user types a query (e.g., "What is our tyre degradation?").
2. **Intent Recognition:** The `jarvis_engine.py` script uses regular expressions and heuristic keyword matching to categorize the intent of the question. It recognizes the keywords "tyre" and "degradation".
3. **Engine Trigger:** JARVIS routes the request to the appropriate backend module—in this case, the `TyreIntelligenceEngine`.
4. **Data Retrieval & Calculation:** The Tyre Engine executes its linear regression on the current stint data and returns a numerical scalar (e.g., `0.084`).
5. **Formatting:** JARVIS wraps the scalar in a readable text template and outputs the answer: "The current tyre degradation slope is 0.084 seconds per lap."

### Evidence Behind Answers
Because JARVIS directly triggers the standard backend engines, its answers are identical to the numbers displayed on the visual dashboards. If JARVIS states the degradation is 0.084, the user will find the exact same number if they manually navigate to the Tyre Intelligence tab. There is no discrepancy between the AI output and the dashboard output.

### Production Status and Limitations
JARVIS is currently classified as **Partially Functional / Experimental**. It is highly effective at answering specific, predefined tactical intents (such as tyre degradation, gap queries, and basic pace queries). However, if a user asks a complex, unstructured query that falls outside its routing logic (e.g., "What is the historical probability of rain at this track in the next 10 minutes?"), the regex router will fail to match an intent. In these cases, JARVIS will fall back to a generic response indicating it cannot process the request. It will not attempt to guess or hallucinate an answer.

---

## 14. JARVIS Query Walkthroughs

To use JARVIS effectively, the engineer must ask questions aligned with its tactical capabilities. Below are realistic examples of how JARVIS processes different types of queries.

### Query: "What is our tyre degradation?"
- **What the user is asking:** The engineer wants to know the mathematical pace loss per lap due to rubber wear.
- **What data is examined:** JARVIS triggers the Tyre module, which isolates the primary driver's current stint lap times, filters outliers, and calculates the linear regression slope.
- **How to interpret the answer:** If JARVIS replies, "Degradation is 0.12s per lap," the engineer knows the tyres are degrading rapidly (a typical rate might be 0.05s).
- **Limitations:** If the driver has only completed 2 laps on the current tyres, the linear regression lacks sufficient data points and the output may be statistically insignificant.

### Query: "Why are we slower?" (Conceptual Example)
- **What the user is asking:** The engineer wants a high-level summary of the time loss compared to a rival.
- **What data should be examined:** JARVIS would need to trigger the Telemetry Performance Lab, compare the two distance arrays, identify the corner with the largest negative VMin differential, and format the output.
- **Current Status:** While the Telemetry Lab performs this calculation natively, routing complex multi-driver telemetry analysis through the JARVIS NLP interface is highly experimental. The engineer is currently better served viewing the visual charts for this specific task.

### Query: "What is the gap to the car behind?"
- **What the user is asking:** The engineer needs an immediate read on the physical distance to the chasing threat.
- **What data is examined:** JARVIS queries the `RaceStateEngine`, which looks up the primary driver's position in the FastF1 timing loop matrix, identifies the driver in `Position + 1`, and calculates the time differential.
- **How to interpret the answer:** If JARVIS replies, "The gap to HAM is 18.5 seconds," the engineer compares this to the 20-second pit loss metric to determine if they can pit without losing position.

### Query: "What is the strategy recommendation?"
- **What the user is asking:** The engineer wants the highest probability outcome from the Monte Carlo simulator.
- **What data is examined:** JARVIS queries the `monte_carlo_engine.py` cache for the strategy candidate with the highest Win Probability.
- **How to interpret the answer:** JARVIS replies, "Optimal strategy: Pit Lap 40 for Hard, Win Prob: 65%." The engineer takes this as the mathematical baseline, but must still account for qualitative factors like driver feedback or impending weather.
"""
    os.makedirs('docs/parts', exist_ok=True)
    with open('docs/parts/part_3.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Part 3 written successfully.")

if __name__ == '__main__':
    generate()
