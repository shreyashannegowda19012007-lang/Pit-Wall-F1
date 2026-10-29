"""
Historical Session Model Validation Script (Phase 6)
Validates core analytical models against real historical sessions.
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

from src.session_utils import parse_session_id
from src.data_ingestion import fetch_session_data
from src.telemetry_analysis_service import TelemetryAnalysisService
from src.tyre_analytics import TyreAnalyticsEngine
from src.probabilistic_service import ProbabilisticService
from src.standings_service import StandingsService

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("validation")

def validate_session(session_id: str, primary_driver: str, ref_driver: str):
    logger.info(f"==================================================")
    logger.info(f"Validating Session: {session_id} ({primary_driver} vs {ref_driver})")
    logger.info(f"==================================================")

    year, event, s_type = parse_session_id(session_id)
    assert year in [2023, 2024], f"Invalid year: {year}"
    logger.info(f"Parsed Session: Year={year}, Event={event}, Type={s_type}")

    # 1. Ingestion Validation
    logger.info("1. Testing Data Ingestion...")
    data = fetch_session_data(year, event, s_type)
    assert data.get("success"), f"Failed to fetch session data: {data.get('error')}"
    laps = data.get("laps")
    assert laps is not None and not laps.empty, "Laps dataframe is empty"
    drivers = laps["Driver"].unique().tolist()
    assert primary_driver in drivers, f"Driver {primary_driver} not in session drivers"
    assert ref_driver in drivers, f"Driver {ref_driver} not in session drivers"
    logger.info(f"  Ingestion passed. Total laps: {len(laps)}, Drivers: {len(drivers)}")

    # 2. Telemetry and Corner Decomposition Validation
    logger.info("2. Testing Telemetry Analysis & Corner Decomposition...")
    comp_res = TelemetryAnalysisService.compare_laps(
        session=data.get("raw_session"),
        target_driver=primary_driver,
        ref_driver=ref_driver
    )
    assert comp_res.get("success"), f"Lap comparison failed: {comp_res.get('error')}"
    corners = comp_res.get("corner_analyses", [])
    assert len(corners) > 0, "No corners detected in corner_analyses"
    c1 = corners[0]
    logger.info(f"  Corner 1 ({c1.get('corner_name')}) Loss: total={c1.get('measured_time_loss_s', 0.0):+.3f}s (Braking: {c1.get('braking_loss_s', 0.0):+.3f}s, Apex: {c1.get('apex_loss_s', 0.0):+.3f}s, Exit: {c1.get('exit_loss_s', 0.0):+.3f}s)")

    # 3. Tyre Degradation Model Validation
    logger.info("3. Testing Tyre Analytics Engine...")
    tyre_res = TyreAnalyticsEngine.analyze_stint_degradation(
        session=data.get("raw_session"),
        driver_id=primary_driver
    )
    assert tyre_res.get("success"), f"Tyre degradation analysis failed: {tyre_res.get('error')}"
    assert tyre_res.get("driver_id") == primary_driver
    deg_rate = tyre_res.get("degradation_slope_s_per_lap")
    assert deg_rate is not None, "Degradation rate is missing"
    r2 = tyre_res.get("r_squared", 0.0)
    logger.info(f"  Tyre Deg Rate: {deg_rate:.4f} s/lap, Compound: {tyre_res.get('compound')}, R²: {r2:.2f}")

    # 4. Strategy & Undercut Analysis
    logger.info("4. Testing Strategy & Undercut Simulation...")
    undercut_res = ProbabilisticService.analyze_undercut_overcut(
        driver_id=primary_driver,
        rival_driver_id=ref_driver,
        gap_s=1.8,
        base_pace_s=81.5,
        rival_base_pace_s=81.8,
        cur_lap=22,
        total_laps=66,
        tyre_compound="MEDIUM",
        tyre_age=16,
        primary_is_ahead=False
    )
    assert undercut_res.get("success"), f"Undercut failed: {undercut_res.get('error')}"
    assert "tactic" in undercut_res, "Tactic missing from undercut analysis"
    assert "undercut_success_probability" in undercut_res, "Undercut probability missing"
    assert 0.0 <= undercut_res["undercut_success_probability"] <= 1.0, "Probability out of range [0, 1]"
    logger.info(f"  Undercut Tactic: {undercut_res['tactic']}, Prob: {undercut_res['undercut_success_probability']:.2%}")

    # 5. Monte Carlo Stochastic Simulation
    logger.info("5. Testing Monte Carlo Stochastic Simulation...")
    mc_res = ProbabilisticService.run_full_field_monte_carlo(
        circuit_id="SPAIN" if "SPAIN" in session_id else "MONACO",
        total_laps=len(laps[laps["Driver"] == primary_driver]),
        num_sims=50
    )
    rankings = mc_res.get("driver_rankings", [])
    assert len(rankings) > 0, "No driver rankings generated"
    top_p = rankings[0]["win_probability_pct"]
    logger.info(f"  MC Simulated 50 races. Projected Winner: {rankings[0]['driver_id']} ({top_p:.1f}% win rate)")

    logger.info(f"Validation for {session_id} PASSED SUCCESSFULLY!\n")

def validate_championship():
    logger.info("Testing Jolpica Standings Service...")
    service = StandingsService()
    driver_st = service.get_driver_standings(2024)
    assert driver_st.get("season") == 2024
    assert len(driver_st.get("standings", [])) >= 20, "Missing driver standings"
    top_d = driver_st["standings"][0]
    logger.info(f"  2024 Championship Leader: {top_d['driver_name']} ({top_d['points']} pts, {top_d['wins']} wins)")

    cons_st = service.get_constructor_standings(2024)
    assert cons_st.get("season") == 2024
    assert len(cons_st.get("standings", [])) >= 10, "Missing constructor standings"
    top_c = cons_st["standings"][0]
    logger.info(f"  2024 Constructors Leader: {top_c['constructor_name']} ({top_c['points']} pts, {top_c['wins']} wins)")
    logger.info("Championship validation PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    try:
        validate_session("S-2024-SPAIN", "VER", "HAM")
        validate_session("S-2023-MONACO", "VER", "ALO")
        validate_championship()
        print("\nALL HISTORICAL SESSION VALIDATIONS PASSED!")
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        sys.exit(1)
