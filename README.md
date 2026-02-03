# Pit-Wall: F1 Tire Degradation Forecaster

Pit-Wall is a predictive analytics engine that identifies the "tire cliff" in Formula 1 racing. By utilizing Deep Learning to analyze non-linear degradation patterns, it provides technical insights that allow teams to optimize pit stop timing and race strategy.

---

## How the Project Works

The system operates as a data-to-decision pipeline, moving from raw telemetry to actionable strategic alerts.

### 1. Data Ingestion & Preprocessing
The engine pulls live or historical telemetry via the **FastF1 API**. 
* **Filtering:** It identifies and removes "dirty air" laps, Safety Car periods, and yellow flag sectors that create noise in tire wear data.
* **Normalization:** Raw lap times are normalized against track temperature and fuel burn to isolate pure mechanical degradation.

### 2. The GRU Predictive Engine
The core is a **Gated Recurrent Unit (GRU)** neural network.
* **Sequence Analysis:** Unlike standard models, the GRU looks at the last 10 laps as a sequence. It learns the "rate of change" in lap times.
* **Inflection Point Detection:** The model predicts the next 5 laps. It specifically looks for the "Cliff"—the moment where the tire's chemical bonds break down and lap times spike by >0.5s.

### 3. Real-Time Inference & API
The trained model is hosted via **FastAPI** in a **Docker** container. This allows the strategy software to query the model every time a driver crosses the finish line.

---

## Utility for F1 Data Analysts

Data analysts spend hours manually plotting degradation slopes. This project automates that workflow:
* **Automated Trend Detection:** Analysts can instantly see if a driver's current stint is matching the predicted degradation curve or if they are "over-driving" the tires.
* **Compound Comparison:** The tool can simulate "what-if" scenarios, comparing how a Hard tire stint would perform versus a used set of Softs based on current track evolution.
* **Data-Driven Debriefs:** Post-race, analysts can use the model to identify exactly where a strategy failed or succeeded based on the predicted vs. actual tire life.

---

## Utility for the Pit Crew & Strategists

In the high-pressure environment of the pit wall, decisions must be made in seconds.
* **The "Pit Window" Alert:** The dashboard provides a visual "Red Zone." When the predicted lap time for the next lap exceeds the "Pit Loss" threshold (the time lost in the pit lane), it triggers a "BOX THIS LAP" recommendation.
* **Undercut/Overcut Validation:** Strategists can see if the tires have enough "life" left to push for an overcut, or if the degradation is so high that an immediate undercut is mandatory.
* **Resource Management:** By predicting the cliff accurately, the pit crew can be alerted precisely when to prepare the next set of tires, reducing the risk of a "stale" tire blanket or a last-second scramble.

---

## Technical Stack
* **Language:** Python 3.10+
* **Deep Learning:** PyTorch / Gated Recurrent Units (GRU)
* **Data Source:** FastF1 API (Telemetry & Timing)
* **Backend:** FastAPI & Uvicorn
* **Deployment:** Docker & GitHub Actions (CI/CD)
* **Visualization:** Streamlit & Plotly
