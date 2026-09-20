import os

def generate():
    content = """# PART VI — REAL ENGINEERING WORKFLOWS

A tool is only as useful as the engineer operating it. This section outlines 8 realistic engineering case studies, demonstrating exactly how a strategist or performance engineer combines the modules of Pitwall F1 to solve complex tactical problems on the fly.

## 28. Case Study 1: Race Strategy Workflow
**Situation:** You are the chief strategist. It is Lap 15 of a 50-lap race. Your driver is in P3, trailing P2 by 1.5 seconds. P2 is trailing the leader (P1) by 4 seconds. Your driver is on Medium tyres.
**Available Data:** Timing Tower gaps, Tyre Degradation slope, Monte Carlo projections.
**Feature Used:** Race Simulator & Strategy Engine.
**Workflow:**
1. You check the Tyre Intelligence module. The degradation slope is `0.06s/lap`.
2. You open the Strategy Engine. The baseline Monte Carlo recommendation states: "Pit Lap 20 for Hard Tyres. Win Probability: 12%."
3. You realize that a 12% win probability is unacceptable; staying on the default strategy will result in a P3 finish.
4. You use the What-If sidebar to test an aggressive Undercut. You set the pit lap to Lap 16 (the very next lap) and select Hard tyres.
5. You click RECALCULATE. The engine runs 250 parallel universes. The new Win Probability jumps to 28%, with an Expected Position (P_exp) of 2.1.
**Engineering Interpretation:** By pitting early, you force P2 and P1 to react. If they stay out on older, slower tyres while your driver is on fresh Hards, your driver will close the gap mathematically. The simulation proves the risk is mathematically viable.
**Decision:** "Box this lap. Box, box."

## 29. Case Study 2: Driver-vs-Driver Analysis
**Situation:** Your driver is consistently losing 0.3 seconds in Sector 2 compared to their teammate in an identical car. The driver claims the car lacks front grip.
**Available Data:** High-frequency speed, throttle, and brake traces.
**Feature Used:** Telemetry Performance Lab.
**Workflow:**
1. Set Primary Driver to your driver, and Reference Driver to the teammate.
2. Isolate the analysis to the Sector 2 boundaries using the Corner Selector.
3. You observe the Speed Trace (top chart) and the Brake Trace (bottom chart).
4. The calculation engine outputs: "Brake Point Delta: +8 meters. VMin Delta: -5 km/h."
5. You look at the throttle trace on corner exit; it is jagged and inconsistent for your driver, while the teammate's is smooth.
**Engineering Interpretation:** The driver is braking 8 meters *later* than their teammate (too deep into the corner). Because they carry too much speed in, they miss the apex, resulting in a minimum speed 5 km/h slower. When they try to accelerate out, the car is off the racing line, causing wheelspin (the jagged throttle trace). The car does not lack front grip; the driver is simply over-driving the entry.
**Decision:** You radio the driver: "Brake earlier into Turn 11. Focus on the exit, you are missing the apex."

## 30. Case Study 3: Tyre Strategy Workflow
**Situation:** The driver radios: "The tyres are gone. We need to pit." The scheduled pit stop is not for another 8 laps.
**Available Data:** Lap times, empirical regression calculations.
**Feature Used:** Unified Tyre Intelligence.
**Workflow:**
1. You ignore the driver's radio message temporarily and look at the mathematical reality.
2. You open the Tyre Intelligence module and observe the degradation slope for the current stint.
3. The slope reads `0.02s/lap`. The lap times are extremely consistent. 
**Engineering Interpretation:** The driver is experiencing a momentary lack of grip (perhaps due to a gust of wind or passing through dirty air), but the mathematical trend proves the physical rubber is perfectly fine. Pitting now would ruin the strategy and drop the car into traffic.
**Decision:** You radio the driver: "Pace is good. Degradation is nominal. Stay out, stick to the plan."

## 31. Case Study 4: Undercut / Overcut Analysis
**Situation:** You are in P2, stuck behind P1. The gap is 0.8 seconds. You cannot overtake on track due to a lack of straight-line speed.
**Available Data:** Track layout, tyre degradation, pit lane time loss.
**Feature Used:** Monte Carlo What-If Simulation.
**Workflow:**
1. You run a What-If scenario pitting on Lap 20 (an Undercut). Win Prob: 45%.
2. You run a What-If scenario pitting on Lap 25 (an Overcut, waiting for P1 to pit first). Win Prob: 15%.
**Engineering Interpretation:** The circuit has high tyre degradation. The fresh tyre pace advantage of the Undercut outweighs the penalty of an extra pit stop. 
**Decision:** You prepare the crew for a Lap 20 Undercut.

## 32. Case Study 5: Safety Car Scenario
**Situation:** A car crashes into the barriers. The Track Status on the Command Center immediately changes to `SAFETY CAR`.
**Available Data:** FastF1 Race Control stream, Gaps.
**Feature Used:** Command Center & Timing Tower.
**Workflow:**
1. When the SC is deployed, the entire field must slow down by roughly 40%. 
2. A normal pit stop costs 20 seconds. Under a Safety Car, because the cars on track are driving so slowly, a pit stop effectively only costs 10-12 seconds of track position.
3. You look at the Timing Tower. The gap to the car behind you is 15 seconds.
**Engineering Interpretation:** You have a "free" pit stop. You can pit for fresh tyres and re-enter the track still ahead of the car behind you, preserving your position while gaining a massive tyre advantage.
**Decision:** "Safety Car deployed. Box for Hards."

## 33. Case Study 6: Traffic Analysis
**Situation:** The Strategy Engine recommends pitting right now. 
**Available Data:** GPS coordinates, Vector headings.
**Feature Used:** 3D Spatial Intelligence Map.
**Workflow:**
1. You don't blindly trust the Strategy Engine. You open the Spatial map.
2. You locate your driver on the track. You mentally project where they will emerge after a 20-second pit stop.
3. You see a cluster of four cars fighting for position exactly at that projected emergence point.
**Engineering Interpretation:** The Strategy Engine calculates mathematical pace, but the Spatial Map reveals physical reality. If you pit now, you will emerge directly behind a DRS train of four cars. You will be stuck and unable to use your fresh tyre pace.
**Decision:** You override the Strategy Engine and delay the pit stop by two laps to allow the traffic cluster to move past the pit exit.

## 34. Case Study 7: Validating an Overtake Threat
**Situation:** You are in P1. P2 is closing in. The gap is 1.2 seconds.
**Available Data:** Overtake Machine Learning model, Speed arrays.
**Feature Used:** Command Center (Overtake Probability) & Telemetry Lab.
**Workflow:**
1. You check the Command Center. The Overtake Probability reads `85%`.
2. You open the Telemetry Lab to understand why. You overlay P1 and P2 on the main straight.
3. You observe the Speed trace. P2's top speed is 330 km/h, while your top speed is 315 km/h.
**Engineering Interpretation:** The ML model is correctly identifying a massive top-speed deficit. Once P2 crosses the 1.0-second threshold and activates DRS, you will be entirely defenseless on the straight.
**Decision:** You instruct the driver to deploy maximum battery deployment (Overtake button) solely on the main straight to defend the position, sacrificing pace in the corners.

## 35. Case Study 8: The JARVIS Quick-Check
**Situation:** It is a chaotic start. You are managing the tyre warmup procedures and radioing the driver. You need to know the gap to P4 immediately, but the Timing Tower is scrolled to the bottom.
**Available Data:** Timing matrices, NLP Router.
**Feature Used:** JARVIS Engineering Assistant.
**Workflow:**
1. Without touching the mouse, you type into the JARVIS terminal: "Gap to P4."
2. JARVIS intercepts the query, parses the `RaceStateEngine`, retrieves the interval, and replies: "The gap to P4 (SAI) is 3.4 seconds."
**Engineering Interpretation:** You instantly have the tactical information required without losing visual focus on the live telemetry traces on your secondary monitor.
"""
    os.makedirs('docs/parts', exist_ok=True)
    with open('docs/parts/part_6.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Part 6 written successfully.")

if __name__ == '__main__':
    generate()
