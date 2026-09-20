import os
import json
from datetime import datetime

def generate_full_markdown():
    try:
        with open('ast_inventory.json', 'r', encoding='utf-8') as f:
            ast_data = json.load(f)
    except FileNotFoundError:
        ast_data = []

    doc = []
    
    # 1. Cover Page
    doc.append("# PITWALL F1 COMPLETE TECHNICAL DOCUMENTATION")
    doc.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc.append("**Status:** Official Engineering Specification")
    doc.append("\n---\n")

    # 2. Executive Summary
    doc.append("## 2. EXECUTIVE SUMMARY")
    doc.append("The Pitwall F1 project is an advanced, telemetry-driven race strategy and visualization dashboard. It ingests FastF1 telemetry data, performs spatial intelligence modeling, evaluates race strategies using Monte Carlo simulations, calculates time loss attribution through differential telemetry math, and presents results in a Streamlit-based UI. The system integrates machine learning for overtake predictions and features an AI-driven 'JARVIS' assistant for querying race parameters. After extensive remediation, it successfully utilizes real telemetry rather than mocked procedural calculations.")
    doc.append("\n---\n")

    # 3. Project Purpose
    doc.append("## 3. PROJECT PURPOSE")
    doc.append("To provide Formula 1 racing engineers and strategists with real-time and historical race data analysis, stochastic strategy modeling, and granular spatial telemetry diagnostics in a unified Command Center interface.")
    doc.append("\n---\n")

    # 4. System Architecture
    doc.append("## 4. SYSTEM ARCHITECTURE")
    doc.append("### Data Flow Architecture")
    doc.append("```mermaid")
    doc.append("graph TD")
    doc.append("    A[User / Streamlit UI] --> B[Pitwall UI (`src/pitwall_ui.py`)]")
    doc_content = """    B --> C[Telemetry API / Probabilistic Service]
    C --> D[Data Ingestion Engine (FastF1 `src/data_ingestion.py`)]
    C --> E[Strategy & Monte Carlo Engine (`src/monte_carlo_engine.py`)]
    C --> F[Telemetry Performance Lab (`src/telemetry_performance_lab.py`)]
    E --> G[Production ML Engine (`src/production_ml_engine.py`)]
    G --> H[Model Loader (`src/model_loader.py`)]
```

### Layers
- **Application Entrypoint:** `src/pitwall_ui.py` (Streamlit loop)
- **UI Layer:** `src/pitwall_ui.py`, `src/ui_elements.py`
- **Orchestration Layer:** `src/probabilistic_service.py`, `src/telemetry_api.py`
- **Data Ingestion Layer:** `src/data_ingestion.py` (FastF1 Cache, FIA APIs)
- **Intelligence Layer:** 
  - `src/spatial_intelligence_engine.py` (3D Mapping)
  - `src/telemetry_performance_lab.py` (Driver Differentials)
  - `src/unified_tyre_intelligence.py` (Degradation Models)
- **Simulation Layer:** `src/monte_carlo_engine.py`, `src/race_simulator.py`
- **ML Layer:** `src/production_ml_engine.py`, `src/model_loader.py`
- **Persistence/Cache Layer:** Local `fastf1` file cache in `track_cache` and `%APPDATA%`
"""
    doc.append(doc_content)
    doc.append("\n---\n")

    # 5. Repository Structure
    doc.append("## 5. REPOSITORY STRUCTURE")
    doc.append("The project resides primarily within the `src/` directory, supported by a `scripts/` directory for offline jobs like ML training.")
    doc.append("```")
    doc.append("D:/Pitwall F1 project/")
    doc.append("├── src/                  # Core Application logic")
    doc.append("├── scripts/              # Offline tools (e.g., train_overtake_model.py)")
    doc.append("├── models/               # Serialized ML Models (e.g., model.pkl)")
    doc.append("├── track_cache/          # FastF1 offline track metadata")
    doc.append("└── docs/                 # Auto-generated documentation")
    doc.append("```")
    doc.append("\n---\n")

    # 6. Complete Feature Catalogue
    doc_content = """## 6. COMPLETE FEATURE CATALOGUE

### Spatial Intelligence Engine
- **Purpose:** Renders the 3D location of all 20 cars.
- **User capability:** Views real-time track map and car gaps.
- **Inputs:** FastF1 X, Y, Z coordinates.
- **Data source:** FastF1 `lap.get_telemetry()`.
- **Processing:** Extracts telemetry at midpoint, computes dx/dy for heading, and maps coordinates.
- **Models:** None (Direct telemetry).
- **Files:** `spatial_intelligence_engine.py`
- **Status:** PRODUCTION / FUNCTIONAL (Refactored from sine/cosine mocks).

### Monte Carlo Strategy Simulator
- **Purpose:** Calculates win probability distributions for pitstop choices.
- **Inputs:** Target compound, pit lap, current grid gaps.
- **Data source:** FastF1 lap time deltas and positions.
- **Processing:** Vectorized numpy simulation sampling from normal/lognormal distributions.
- **Files:** `monte_carlo_engine.py`, `race_simulator.py`
- **Status:** PRODUCTION / FUNCTIONAL

### Telemetry Performance Lab
- **Purpose:** Attributes corner time loss.
- **Processing:** Aligns two drivers' arrays by distance, filters by corner bounds, computes deltas for VMin and Peak Brake.
- **Files:** `telemetry_performance_lab.py`
- **Status:** PRODUCTION / FUNCTIONAL

### Overtake ML Engine
- **Purpose:** Predicts success probability of an overtake.
- **Processing:** Loads `model.pkl` and infers against gap, DRS, and speed delta.
- **Models:** RandomForestClassifier
- **Files:** `production_ml_engine.py`, `model_loader.py`
- **Status:** PRODUCTION / FUNCTIONAL

### JARVIS AI Intelligence
- **Purpose:** AI assistant for pitwall insights.
- **Processing:** Intent routing via Regex/heuristics to internal engine calls.
- **Files:** `jarvis_engineering_insights.py`
- **Status:** EXPERIMENTAL / PARTIALLY FUNCTIONAL

### Unified Tyre Intelligence
- **Purpose:** Tyre degradation forecasting.
- **Processing:** Calculates slope of empirical lap times using np.polyfit.
- **Status:** PARTIALLY FUNCTIONAL (Thermal model is heuristic/synthetic)

"""
    doc.append(doc_content)
    
    # 7 to 20...
    doc_content = """
## 7. DATA ARCHITECTURE & 8. FASTF1 INGESTION
- **Provider:** FastF1 API
- **Pipeline:** `data_ingestion.py` -> `fetch_session_data(year, event, session_type)`
- **Cache:** Stored locally in `track_cache` to avoid repeated FIA API hits.
- **Extracted Fields:** Distance, X, Y, Z, Speed, Throttle, Brake, nGear, DRS, Time, LapNumber, Position.

## 9. TELEMETRY ENGINEERING
- **Time Loss Attribution:** Extracts arrays for Driver A and B, subsets by Corner Distance bounds, calculates `Speed.min()`, `Brake.max()`, and overall time integration over distance. Implementation in `telemetry_performance_lab.py`.

## 10. STRATEGY ENGINE & 11. MONTE CARLO
- **Simulations:** Default 250 iterations (vectorized).
- **Stochastic Noise:** Uses `np.random.default_rng(seed)` for Thread-Safe Normal (Pace Noise) and Lognormal (Pit Stop Duration Noise).
- **Ranking:** Strategies are ranked by "MAX_WIN_PROBABILITY".

## 12. MACHINE LEARNING & 13. REINFORCEMENT LEARNING
- **Active ML Model:** `models/overtake_probability/model.pkl` (RandomForestClassifier).
- **Training Pipeline:** `scripts/train_overtake_model.py` generates synthetic overtake data (delta v, DRS state) and trains the scikit-learn model.
- **RL System:** Mentioned in `f1_strategy_env.py` and `rl_strategy_agent.py` but currently **EXPERIMENTAL/ORPHANED** from the main UI orchestration loop.

## 18. WHAT-IF SCENARIO ENGINE
- **Control:** Sidebar inputs for Compound and Pit Lap.
- **Backend Response:** Injects a custom `StrategyPlan` into the Monte Carlo queue. Overrides the `st.session_state` and invokes `mc_engine.simulate_strategy_vectorized()`. Confirmed functional.

## 21. DATA PROVENANCE
- **REAL SOURCE DATA:** FastF1 Lap Times, X/Y/Z Telemetry, Position Gaps.
- **DERIVED FROM REAL DATA:** Corner Min Speeds, Brake Points.
- **ML OUTPUT:** Overtake Probability.
- **STATISTICAL CALCULATION:** Win Probability, Expected Finish Position.
- **SYNTHETIC/HEURISTIC:** Tyre Core/Bulk Temperatures.
- **UNAVAILABLE:** Compound Crossover Lap.

## 27. RUN INSTRUCTIONS
- **Launch Command:** `python -m streamlit run src/pitwall_ui.py`
- **Environment:** Requires `numpy`, `pandas`, `scikit-learn`, `fastf1`, `streamlit`. Python 3.9+ recommended.
"""
    doc.append(doc_content)

    # 29. Complete File Reference
    doc.append("## 29. COMPLETE FILE/FUNCTION REFERENCE")
    if ast_data:
        for file in ast_data:
            path = file['path']
            basename = os.path.basename(path)
            doc.append(f"### `{basename}`")
            doc.append(f"- **Path:** `{path}`")
            classes = [c['name'] for c in file['classes']]
            if classes:
                doc.append(f"- **Classes:** {', '.join(classes)}")
            funcs = [f['name'] for f in file['functions']]
            if funcs:
                doc.append(f"- **Functions:** {', '.join(funcs)}")
            doc.append("\n")
    else:
        doc.append("*AST File Data Not Found. See manual inventory.*")

    os.makedirs('docs', exist_ok=True)
    with open('docs/PITWALL_F1_COMPLETE_TECHNICAL_DOCUMENTATION.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(doc))

if __name__ == '__main__':
    generate_full_markdown()
