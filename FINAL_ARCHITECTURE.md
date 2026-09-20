# FINAL ARCHITECTURE DOCUMENTATION — RED BULL F1 PLATFORM v2.4.0

```text
                               DATA SOURCES (OpenF1 / FastF1)
                                             │
                                             ▼
                       INGESTION & DEDUPLICATION (`EventIdempotencyRegistry`)
                                             │
                                             ▼
                        AUTHORITATIVE RACE STATE (`UnifiedRaceState` v2.4.0)
                                             │
      ┌──────────────────────┬───────────────┴───────────────┬──────────────────────┐
      ▼                      ▼                               ▼                      ▼
TYRE PHYSICS ENGINE   DECISION ENGINE                 PRODUCTION ML ENGINE     SPATIAL ENGINE
(3-Layer Thermal PDE) (FIA Rules / Undercut)          (P10/P50/P90 + SHAP)    (3D Mesh + Cockpit)
      │                      │                               │                      │
      └──────────────────────┴───────────────┬───────────────┴──────────────────────┘
                                             ▼
                             VECTORIZED MONTE CARLO SIMULATOR
                                (1,000 to 100,000 SIMD Runs)
                                             │
                                             ▼
                              JARVIS AI ENGINEER INTERFACE
                           (20 Tools + Grounded Citations)
                                             │
                                             ▼
                               STREAMLIT MASTER WORKSTATION UI
```

---

## Component Architecture Sitemap
- `src/realtime_live_infrastructure.py`: Real-Time Live Infrastructure, Latency Monitor, Event Bus, Deduplication.
- `src/spatial_intelligence_engine.py`: 3D Spatial Circuit Mesh, 20-Car Spatial Positions, Cockpit POV Camera.
- `src/production_data_platform.py`: SessionPreparationManager, SHA-256 Manifests, ProductionCacheManager.
- `src/production_hardening_engine.py`: InputSanitizer, RateLimiter, AIBoundaryGuard, FaultToleranceEngine, SystemHealthService.
- `src/system_integration_validator.py`: SystemIntegrationValidator auditing all 39 subsystems.
- `src/pitwall_ui.py`: Master Pit-Wall Workstation UI Shell, Layout Presets, Keyboard Shortcuts.
- `src/telemetry_api.py`: Global REST & Service Singleton Router.
