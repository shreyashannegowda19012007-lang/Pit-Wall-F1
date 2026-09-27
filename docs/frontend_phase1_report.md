# Pitwall F1 — Frontend Modernization Phase 1 Report

## Architecture Chosen
We elected to use **React 19 + TypeScript + Vite** for a modern, performant, and type-safe frontend shell, combined with **React Router** for client-side routing. For styling, we implemented a **Vanilla CSS** design system utilizing CSS variables. This approach maximizes control over the application's unique, high-quality F1 engineering aesthetic while minimizing external dependencies like Tailwind.

## Files Created/Changed
1. **`src/main_api.py` (Modified)**: Added three new lightweight endpoints (`/api/timing/summary`, `/api/telemetry/profile/{driver_id}`, `/api/strategy/summary`) wrapping the existing authoritative `api_service`.
2. **`frontend/src/main.tsx` (Modified)**: Configured `BrowserRouter` to bootstrap the application.
3. **`frontend/src/App.tsx` (Modified)**: Established the application route tree linking the Landing page and App Dashboard.
4. **`frontend/src/index.css` (Modified)**: Implemented the F1 race-engineering design system containing typography, sizing, layout utilities, and reusable components (buttons, badges, cards).
5. **`frontend/src/pages/LandingPage.tsx & .css` (New)**: Constructed the high-quality product entry point with a strong F1 engineering visual identity.
6. **`frontend/src/layouts/AppLayout.tsx & .css` (New)**: Built the primary application shell containing persistent sidebar navigation, topbar session/driver selectors, and live API connection status.
7. **`frontend/src/pages/OverviewPage.tsx & .css` (New)**: The main dashboard connecting to real Python backend endpoints.
8. **`frontend/src/pages/PlaceholderPage.tsx` (New)**: A fallback component for Phase 2 product areas.
9. **`frontend/playwright.config.ts` (New)**: Configuration for browser-level automation testing.
10. **`frontend/tests/pitwall.spec.ts` (New)**: Automated test suite validating critical navigation flows and component rendering.

## Routes/Views Implemented
- `/` - Landing Page
- `/app` - Base Application Shell
- `/app/` - Overview Dashboard (Real data connections)
- `/app/live` - Live Session Dashboard (Phase 2 Placeholder)
- `/app/telemetry` - Telemetry Analysis (Phase 2 Placeholder)
- `/app/comparison` - Driver Comparison (Phase 2 Placeholder)
- `/app/strategy` - Race Strategy (Phase 2 Placeholder)
- `/app/monte-carlo` - Monte Carlo Simulation (Phase 2 Placeholder)
- `/app/replay` - 3D Replay (Phase 2 Placeholder)
- `/app/tyres` - Tyre Intelligence (Phase 2 Placeholder)
- `/app/ml-lab` - ML Lab (Phase 2 Placeholder)
- `/app/jarvis` - JARVIS AI (Phase 2 Placeholder)
- `/app/circuits` - Circuits Metadata (Phase 2 Placeholder)
- `/app/drivers` - Drivers & Teams (Phase 2 Placeholder)

## Real Backend Connections Made
The new frontend is actively consuming the existing verified Python backend via these connections:
- **`GET /api/health`**: Verifies core backend connectivity and displays active status in the App topbar.
- **`GET /api/timing/summary`**: Retrieves the active session manifest (`api_service.get_session_manifest`).
- **`GET /api/telemetry/profile/{driver_id}`**: Retrieves the driver's performance profile (`api_service.get_driver_performance_profile`).
- **`GET /api/strategy/summary`**: Retrieves canonical strategy state (`api_service.get_canonical_strategy_state`).

*Note: The backend maintains its integrity as the source of truth; no business logic was duplicated.*

## Browser Tests Executed
Using **Playwright**, the following tests pass on the Chromium browser:
1. `landing page loads and navigation works`: Verifies hero text visibility and successful routing to `/app`.
2. `session and driver selection`: Verifies driver dropdown interacts correctly and context updates seamlessly.
3. `navigation to product areas renders placeholders or content`: Verifies that side navigation (e.g., JARVIS, Race Strategy) routes correctly and renders appropriate placeholders.

## Known Limitations
- The Overview dashboard currently implements basic, unformatted JSON dumping for `strategy` and `telemetry` objects because the exact schema return shape was not completely mapped to precise UI charts in Phase 1.
- Global application context (session/driver state) is passed natively through React Router's `<Outlet context />` rather than a dedicated state manager (like Redux or Zustand). As the app scales, a state management solution will be required.

## Commands to Run the Environment
1. **Start the Backend Data Engine** (from project root):
   ```bash
   .\.venv\Scripts\python.exe src\main_api.py
   ```
2. **Start the Frontend Application** (from `frontend` directory):
   ```bash
   npm run dev
   ```
