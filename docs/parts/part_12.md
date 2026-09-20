# PART XII — DEPLOYMENT, ENVIRONMENT, AND TROUBLESHOOTING

To ensure that the 40+ pages of engineering workflows can actually be executed, this final addendum covers the technical requirements, environment setup, and common troubleshooting steps for running Pitwall F1 in a production or development setting.

## 65. Environment and Dependencies

Pitwall F1 is highly dependent on specific Python library versions. Attempting to run the platform on an outdated or mismatched environment will cause catastrophic matrix alignment failures in the backend.

### Core Dependencies
- **Python:** 3.10 or higher. The backend relies heavily on structural pattern matching and advanced typing introduced in modern Python versions.
- **FastF1:** The engine requires `fastf1 >= 3.0.0`. Older versions of FastF1 used a completely different caching architecture and a deprecated Ergast API endpoint which will cause the `INITIALIZE UPLINK` function to fail instantly.
- **Pandas & NumPy:** Essential for the vectorization in the Monte Carlo engine and the DataFrames in the telemetry pipeline.
- **SciPy:** The `telemetry_performance_lab.py` script specifically requires `scipy.interpolate` to align the distance arrays.
- **Scikit-Learn:** Required by the `production_ml_engine.py` to deserialize and execute the `model.pkl` Random Forest model.
- **Streamlit:** The entire frontend orchestration relies on Streamlit's reactive execution model.

## 66. Data Caching and Storage Management

Because Pitwall F1 downloads high-frequency telemetry for 20 cars over 50-70 laps, the data footprint is massive.

### The `track_cache` Directory
When a session is successfully initialized, FastF1 serializes the raw API payload into a SQLite database or parquet files stored within the local `track_cache` folder. 
- A single race session can consume between 50MB and 150MB of disk space.
- If a user analyzes an entire 24-race season, the cache will quickly exceed 3GB.

### Cache Corruption
If the FIA API drops a packet during the initial download, the cached file will be permanently corrupted. When Pitwall F1 attempts to load this session in the future, it will throw an `IndexError` or a `KeyError` when attempting to build the arrays.
**The Solution:** The user must manually navigate to the `track_cache` directory and delete the files associated with the corrupted event. The next time the user clicks `INITIALIZE UPLINK`, the system will fetch a fresh, clean payload from the FIA servers.

## 67. Common Troubleshooting Scenarios

### Issue: "The 3D Spatial Map is completely blank."
- **Diagnosis:** The spatial map requires X and Y GPS arrays. 
- **Solution:** Check the year of the session. If it is prior to 2018, the FIA did not consistently broadcast public GPS data. The system is functioning correctly by rendering a blank map rather than hallucinating coordinates. If it is a modern race, the cache may be corrupted (see above).

### Issue: "The Strategy Engine UI freezes when I press RECALCULATE."
- **Diagnosis:** CPU Bottleneck in the Monte Carlo simulator.
- **Solution:** The `monte_carlo_engine.py` utilizes `numpy` vectorization. However, if the host machine has a low-power CPU or insufficient RAM, running 250 universes will block the main Streamlit thread. A developer can enter the backend script and lower the `num_simulations` parameter from 250 to 50 to drastically improve UI responsiveness, at the cost of statistical confidence.

### Issue: "The Overtake Probability always reads 0%."
- **Diagnosis:** Deserialization failure or Feature Shape mismatch.
- **Solution:** Ensure that the Scikit-Learn version installed in your Python environment exactly matches the version used to train `model.pkl`. If the versions mismatch, the model will fail to load silently, and the `production_ml_engine.py` exception handler will return a fallback scalar of 0.0 to prevent a frontend crash.

*End of Document.*
