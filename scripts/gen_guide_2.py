import os

def append_guide():
    brain_dir = r"C:\Users\shrey\.gemini\antigravity-ide\brain\92b2ed6d-dcdf-4c50-aba2-10fae85f4f39"
    dashboard_img = os.path.join(brain_dir, "guide_dashboard_1789304734355.png").replace("\\", "/")
    
    doc = []

    # 5. THE PITWALL F1 INTERFACE (Screen by screen)
    doc.append(f"""# 4. THE PITWALL F1 INTERFACE

This chapter documents the website exactly as you will encounter it, screen by screen.

## SCREEN 1: COMMAND CENTER (MAIN DASHBOARD)

![Command Center]({dashboard_img})

### PURPOSE
To provide an instantaneous, high-level overview of the entire race state, ensuring the strategist has total situational awareness without needing to dig into complex sub-menus.

### FIRST IMPRESSION
You will see a large, dark-themed control panel dominated by a "Timing Tower" on the left, top-level metrics in the center, and a summary of the AI/ML predictions on the right.

### SIDEBAR (SESSION PARAMETERS)
- **Year / Event / Session dropdowns:** Used to query the FIA FastF1 database.
- **INITIALIZE UPLINK button:** Triggers the backend `data_ingestion.py` module to parse the session.
- **Status Indicator:** Shows whether the system is loading or ready.

### MAIN CONTENT (TOP METRICS)
- **Track Status:** Indicates Green Flag, Yellow Flag, Safety Car, or VSC. Sourced directly from FastF1 Race Control messages.
- **Air Temp / Track Temp:** Environmental metrics. Sourced from FastF1 weather data. Crucial for understanding tyre thermal behavior.
- **Overtake Probability:** (e.g., 72%). This is an ML-driven output. It is powered by `production_ml_engine.py`, which evaluates the speed delta and gap of the primary driver to the car ahead using a Random Forest Classifier.

### THE TIMING TOWER
The left column displays the complete running order.
- **Position (P1, P2...):** Current standing.
- **Driver Code (VER, HAM...):** Standard FIA 3-letter abbreviation.
- **Gap:** The time interval to the car ahead in seconds. 
- **Tyre:** The compound currently fitted (Soft, Medium, Hard, Wet).
- **Laps:** The age of the current tyre stint.

#### Engineering Interpretation
A strategist uses the Timing Tower to find "Clean Air" (a gap in traffic where a driver can pit and emerge without being held up by slower cars). If VER is leading by 20 seconds, and a pit stop costs 18 seconds, VER has a "Pit Window" and can pit without losing the lead.

---
<div style="page-break-after: always;"></div>
""")

    # 6. TELEMETRY LAB
    doc.append("""## SCREEN 2: TELEMETRY PERFORMANCE LAB

### PURPOSE
To understand exactly where and why one driver is faster than another, down to the millimeter.

### FIRST IMPRESSION
You will see input selectors for two drivers and a series of complex line charts overlaying two different colored traces.

### TOP AREA
- **Primary Driver Selector:** The driver you want to coach or analyze.
- **Reference Driver Selector:** The target (usually a faster teammate or a direct rival).
- **Corner/Sector Selector:** Allows you to zoom the graphs into a specific area of the track (e.g., Turn 4).

### CHARTS

#### Speed vs Distance
- **X-axis:** Track Distance in meters.
- **Y-axis:** Speed in km/h.
- **Lines:** Two lines, one for each driver.
- **What it means:** A higher line means the driver is traveling faster at that exact point on the track. If Driver A's line dips earlier than Driver B's, Driver A has hit the brakes sooner.

#### Throttle & Brake Application
- **X-axis:** Track Distance in meters.
- **Y-axis:** Percentage (0-100%).
- **What it means:** Shows exactly how aggressively the driver is interacting with the pedals. 

### UNDER THE HOOD: TIME LOSS ATTRIBUTION
This is where Pitwall F1 excels over basic timing screens. The backend `telemetry_performance_lab.py` engine performs the following:
1. It pulls the raw `X,Y,Z,Speed,Time` arrays for the fastest lap of both drivers.
2. It interpolates the data to ensure both arrays align perfectly by track distance.
3. It segments the arrays based on the bounding distances of the selected corner.
4. It mathematically calculates the **VMin** (Minimum Speed) and the **Braking Point Delta** (difference in meters where brake pressure > 10%).

#### Engineering Interpretation
If the engine reports: "Driver loses 0.15s in Turn 4 due to early braking (delta: -12 meters)", the performance engineer can immediately radio the driver: "You are braking 12 meters earlier than your teammate into Turn 4. Carry more speed in."

---
<div style="page-break-after: always;"></div>
""")

    with open('docs/PITWALL_F1_COMPLETE_USER_GUIDE.md', 'a', encoding='utf-8') as f:
        f.write("".join(doc))

if __name__ == '__main__':
    append_guide()
