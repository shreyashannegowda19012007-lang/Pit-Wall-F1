# Pitwall F1 Platform Architecture & Data Lineage Guide

## 1. System Architecture Diagram

```
                 FRONTEND (Streamlit `src/pitwall_ui.py`)
                     │
                     ▼
             FASTAPI API (`src/telemetry_api.py`)
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
      TELEMETRY   STRATEGY    AI ENGINE
      SERVICES    SERVICES     SERVICES
          │          │          │
          └──────────┼──────────┘
                     ▼
       DATA LAYER (`src/database_migrations.py`)
                     │
                     ▼
          POSTGRESQL / SQLITE DATABASE
```

## 2. Data Lineage Metadata Standard
Every analytical artifact produced by the system includes explicit lineage metadata:
- `dataset_version`: Dataset identifier & SHA256 content hash.
- `processing_version`: Time-series pipeline processing version (`v2.4.0`).
- `feature_version`: Telemetry feature extraction schema version (`v2.4.0`).
- `model_version`: Monte Carlo simulation & Bayesian model version (`v2.4.0`).
- `decision_engine_version`: Decision engine optimization version (`v2.4.0`).

## 3. Local Development Quickstart with Docker Compose

1. **Copy Environment Variables**:
   ```bash
   cp .env.example .env
   ```

2. **Launch Docker Services**:
   ```bash
   docker compose up --build
   ```

3. **Run Database Migrations & Seed Demo Data**:
   ```bash
   python -m src.seed_demo_data --seed 42
   ```

4. **Execute Full Test Suite**:
   ```bash
   pytest
   ```
