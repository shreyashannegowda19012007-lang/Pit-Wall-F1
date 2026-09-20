import os

def generate():
    content = """# PART IV — DATA AND ENGINEERING

This section explains the origin, structure, and processing of the data that fuels Pitwall F1. A strategy recommendation is mathematically useless if the engineer does not understand the provenance of the numbers supporting it.

## 15. Where Pitwall Gets Its Data

Pitwall F1 is not a self-contained simulation video game; it is an analytical wrapper around real-world data. 

### The Primary Source: FastF1
The foundational data source for Pitwall F1 is the open-source `FastF1` library. FastF1 interfaces directly with the FIA's public timing APIs (Ergast and the F1 Live Timing SignalR stream) to download the exact same data feeds that the broadcast networks and teams receive during a session. 

When you initialize an uplink in the Command Center, Pitwall F1 does not generate fake data. It requests the official API data for that specific historical event and caches it locally on your hard drive (in the `track_cache` directory) to ensure subsequent loads are instantaneous.

### Data Availability and Quality
The quality of Pitwall's analysis is strictly bound by the quality of the FastF1 data. 
- Modern races (2018–present) generally possess high-fidelity GPS arrays (X, Y, Z coordinates) and high-polling telemetry (Speed, RPM). 
- Older historical sessions may lack spatial GPS data entirely. 
If the API fails to return a specific data structure, Pitwall F1 is designed to gracefully degrade that specific feature (e.g., disabling the 3D map) rather than crashing or inventing coordinates.

---

## 16. The Telemetry Pipeline

How does a signal broadcast from a Formula 1 car's sensor become a red line on a chart? The transformation pipeline is a multi-step process.

**1. Data Acquisition**
The car transmits sensor data via telemetry bursts to the pitwall, which the FIA intercepts and broadcasts to the timing APIs. Pitwall F1 (via FastF1) downloads this raw array. At this stage, it is simply a massive pandas DataFrame containing timestamps and raw integers.

**2. Session Loading & Driver Selection**
When the user selects two drivers (Primary and Reference) in the Telemetry Lab, Pitwall queries the DataFrame to extract only the laps belonging to those drivers. It specifically isolates the "fastest lap" of their current stint to ensure a fair comparison.

**3. Cleaning and Interpolation**
The raw telemetry is imperfect. The sensors may poll at slightly different intervals, or packets may be dropped. Furthermore, Driver A completes the lap in 80 seconds, while Driver B completes it in 82 seconds. The timestamps do not align. 
The Pitwall backend performs a critical mathematical operation here: **Interpolation by Distance**. It resamples both arrays, forcing the data points to map to a standardized *Track Distance* (e.g., every 5 meters) rather than a timestamp.

**4. Analysis and Bounding**
If the user selects a specific corner (e.g., Turn 4), the engine looks up the known start and end track distances for that corner (e.g., 1200m to 1400m). It slices the interpolated arrays to only include data within this bounding box.

**5. Visualization**
The final, clean, aligned, and bounded arrays are pushed to the frontend, where Streamlit renders them using the graphing libraries, presenting the user with the intuitive Speed vs. Distance overlay.

---

## 17. Timing Data

Timing data is the macroscopic view of the race. It is the absolute truth of who is winning and losing.

### Lap Times and Sector Times
The circuit is divided by three physical timing lines, splitting the track into Sector 1, Sector 2, and Sector 3. As the car crosses a line, a timestamp is recorded. 
- A **Sector Time** is the duration spent within that specific boundary.
- A **Lap Time** is the sum of the three sectors.
Pitwall F1 uses these times to calculate the Base Pace of a driver for the Monte Carlo simulator.

### Gaps and Intervals
- **Interval:** The time difference between a car and the car immediately ahead of it.
- **Gap (to Leader):** The time difference between a car and the driver in P1.
These metrics are critical for identifying traffic and pit windows. Pitwall relies on these measured gaps to determine if an undercut is viable.

---

## 18. Telemetry Data

Telemetry data is the microscopic view of the race. It explains *how* the lap time was achieved.

### Major Telemetry Channels
- **Speed (km/h):** The absolute velocity of the car. The most critical channel for identifying time loss.
- **Throttle (0-100%):** The pressure applied to the accelerator pedal. Engineers look for a smooth application of throttle on corner exit. A choppy throttle trace indicates the driver is struggling with rear grip.
- **Brake (Binary or Percentage):** The pressure applied to the brake pedal. Engineers look at the exact track distance where this trace spikes to determine who is braking later into a corner.
- **RPM & Gear:** Indicates engine state. Useful for diagnosing if a driver is using the wrong gear through a complex corner, leading to a loss of torque.
- **DRS (Drag Reduction System):** An integer state (e.g., 0, 8, 10, 12, 14) indicating whether the rear wing flap is closed, armed, or open. Crucial for understanding why a speed trace suddenly spikes on a straight.

---

## 19. Track Data

Track data provides the spatial context for the telemetry.

- **Track Distance:** The total distance around the circuit (e.g., 5,412 meters). All telemetry in Pitwall F1 is anchored to this distance metric to allow cross-driver comparison.
- **Coordinates (X, Y, Z):** The GPS location of the car. `X` and `Y` map the 2D plane (used by the 3D Spatial Intelligence module to render the track map). `Z` represents elevation, which is less tactically relevant but critical for suspension engineering.
- **Corner Regions:** Pitwall maintains an internal mapping of where corners exist on the track distance timeline (e.g., Turn 1 is located between 300m and 450m).

---

## 20. Race Control Data

Race Control messages act as global modifiers that alter the rules of the simulation.

- **Safety Car (SC) / Virtual Safety Car (VSC):** When deployed, all cars must reduce their speed by a mandated percentage. Pitwall's strategy engine monitors these messages. If a SC is active, the time lost by driving through the pit lane is effectively halved, dramatically increasing the Win Probability of a pit stop strategy.
- **Yellow / Red Flags:** Indicate localized or global session suspensions. 
Pitwall pulls these messages from the FastF1 `race_control` stream to ensure the UI Track Status accurately reflects reality.
"""
    os.makedirs('docs/parts', exist_ok=True)
    with open('docs/parts/part_4.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Part 4 written successfully.")

if __name__ == '__main__':
    generate()
