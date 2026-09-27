# Goal Description
Complete Phase 6 Final Adversarial Release Gate. Revert manipulated tests, implement robust parameterized strategy logic, address UI timeouts cleanly, and present truthful verification results without falsified simulated inputs.

## User Review Required
No open questions. Please approve the plan so execution can begin.

## Proposed Changes

### Strategy Engine and Tests
- **[MODIFY] `src/probabilistic_service.py`**:
  - Revert the hardcoded `base_pace_s + 0.5` manipulation.
  - Return the logic to calculate undercut/overcut strictly on provided parameters without hacking the rival pace.
  - Fix the threshold for tactic recommendation to be mathematically sound.
- **[MODIFY] `tests/test_authoritative_strategy_engine.py`**:
  - Replace the single brittle expectation (`assertEqual(uo["recommended_tactic"], "EXECUTE_UNDERCUT")`) with a robust parameterized test.
  - Cover scenarios: Primary driver faster than rival, slower than rival, equal pace, missing/invalid pace, different gaps, and different tyre degradations.
  - Check that the returned tactic rationally corresponds to the simulated inputs (e.g. if rival is much faster, tactic may correctly be `STAY_ON_CURRENT_PACE`).

### Frontend Timeout & UX Handling
- **[MODIFY] `frontend/src/pages/TyresPage.tsx`**:
  - Implement a bounded failure state using `AbortController` (e.g., 60-second timeout).
  - Implement an honest progress loading state with an interval that informs the user: "Connecting...", "Fetching Telemetry Data (This may take up to 2 minutes on cold start)...", "Applying Regression Model...".
  - Gracefully catch `AbortError` and show a "Request Timed Out" UI.
- **[MODIFY] `frontend/src/pages/ReplayPage.tsx`**:
  - Implement the same bounded failure state (AbortController).
  - Add stepped loading text to inform users during long initial requests.
- **[MODIFY] `frontend/tests/pitwall.spec.ts`**:
  - Verify that the Playwright tests now correctly wait for the UI's loading states without timing out arbitrarily. Playwright will be configured to handle the new bounded failure UI if the cache is completely cold, or wait up to the bounded failure time. We will run cold and warm cache tests.

### Delivery
- **[MODIFY] `docs/phase6_final_release_gate.md`**:
  - Create the final report containing exact test results (cold and warm cache), strategy validations, and git hash.

## Verification Plan
### Automated Tests
- `pytest tests/test_authoritative_strategy_engine.py -v` (Should pass parameterized scenarios).
- `npx playwright test` (Should pass or cleanly hit bounded failure states instead of hanging Playwright).
- `npm run build` (Ensures frontend remains clean).

### Manual Verification
- Will trigger cold-cache and warm-cache API hits to confirm the bounded failure state works on cold cache, and the successful UI renders on warm cache.
