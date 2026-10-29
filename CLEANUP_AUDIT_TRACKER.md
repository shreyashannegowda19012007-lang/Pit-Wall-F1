# Pitwall F1 Comprehensive Codebase Cleanup & System Audit Tracker

## Execution Phase Checklist
- [x] **Phase 1: Repository Inventory and Baseline** (Inventoriest entry points, test baselines, and established 100% test passing state)
- [x] **Phase 2: Code Cleanup** (Removed unused logic, fixed unhandled exceptions, eliminated circular imports, unified async data handling)
- [x] **Phase 3: Backend and Model Correctness** (Audited schemas, OLS wear models, Bayesian updating, Monte Carlo probability invariants, Jolpica & OpenF1 endpoints)
- [x] **Phase 4: Frontend Functionality Audit** (Added CSV & Brief exports, fixed buttons, routes, tabs, and removed fabricated fallback data)
- [x] **Phase 5: Driver & Session Consistency** (Verified context synchronization across primary/reference drivers, session uplinks, and session switching)
- [x] **Phase 6: UI/UX Cleanup & Polish** (Enhanced dark engineering styling, unified typography, responsive cards, driver headshots, and team brand colors)
- [x] **Phase 7: Performance and Reliability** (FastF1 SQLite/Parquet local cache verification, optimized bundle size: Vite build in 310ms)
- [x] **Phase 8: Automated Testing Suite** (248/248 pytest unit/integration/model tests passing, 0 errors in TypeScript `tsc -b && vite build`)
- [x] **Phase 9: End-to-End Browser Verification** (Interactive browser subagent verification across all 10 engineering routes on Chrome)
- [x] **Phase 10: Final Clean-State Verification** (Clean production build, zero regressions, all endpoints and exports operational)

---

## Issue & Remediation Tracker

| ID | Category | Component / File | Severity | Issue Description | Root Cause | Fix Status | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **C1** | Cleanup | `src/` modules | Low | Unused imports and broad exception clauses (`except Exception: pass`) | Legacy prototype code suppressing errors silently | Resolved | Replaced with structured logging and domain error handling; 248 pytest tests passing |
| **C2** | UI/UX | `frontend/src/pages/` | Medium | Inconsistent card heights and potential horizontal overflows on smaller screens | Lack of unified CSS layout flex/grid constraints | Resolved | Standardized card-engineering flex heights and responsive overflow wrapping |
| **C3** | Functionality | `frontend/src/pages/LivePage.tsx` | Medium | Live pit-wall status, radio/race control polling, and timing tower connection | Hardcoded fake driver rows and static weather when offline | Resolved | Replaced with honest standby indicators & real session replay classification |
| **C4** | Functionality | `frontend/src/pages/CircuitsPage.tsx` | Medium | Calendar round detail loading & track map modal display | Check endpoint contract and circuit imagery fallback | Resolved | Verified all 24 championship rounds render with circuit specs in browser |
| **C5** | Functionality | `frontend/src/pages/DriversPage.tsx` | Medium | Standings toggle (Drivers vs Constructors) and profile cards | Only session grid was displayed without championship standings | Resolved | Added DRIVERS CHAMPIONSHIP and CONSTRUCTORS CHAMPIONSHIP tabs via Jolpica Ergast |
| **C6** | Functionality | Reports & Exports | Medium | Exporting telemetry / strategy reports to CSV / JSON / PDF | Missing export endpoints and UI download triggers | Resolved | Created `src/report_service.py` and added EXPORT CSV / EXPORT BRIEF buttons in Telemetry, Comparison, and Strategy pages |
| **C7** | Consistency | `frontend/src/contexts/PitwallContext.tsx` | Medium | Driver list reactivity when switching rounds or seasons | Ensure driver list refreshes immediately upon Uplink or session change | Resolved | Verified dynamic reactive updates upon selecting drivers (HAM/NOR) and uplinking sessions |
| **C8** | Architecture | `src/main_api.py` & `src/data_providers.py` | Low | Centralized error handling and standardized response wrappers | Some routes raise raw HTTPException without unified error JSON format | Resolved | Unified API error responses and schema-compliant outputs |
