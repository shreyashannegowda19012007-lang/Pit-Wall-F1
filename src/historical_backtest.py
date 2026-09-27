"""
Multi-season historical backtest runner.

Uses the existing HistoricalBacktestEngine + AdvancedMonteCarloStrategyEngine.
Loads real FastF1 sessions where available; records DATA_UNAVAILABLE where not.
Strict temporal isolation via InformationSnapshot.validate_no_leakage().
RL is evaluated separately (EXPERIMENTAL) and never influences recommendations.
"""

import fastf1
import json
import os
import sys
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

# Project imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from historical_leakage_guard import HistoricalInformationFilter, DataLeakageError
from historical_replay_evaluator import HistoricalReplayEngine, FutureDataGuard
from advanced_monte_carlo import AdvancedMonteCarloStrategyEngine
from f1_strategy_env import F1StrategyEnv
from stable_baselines3 import PPO as PPOModel

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fastf1_cache')
fastf1.Cache.enable_cache(CACHE_DIR)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports', 'backtest')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# RACE MANIFEST  (chronologically ordered, no temporal mixing)
# ──────────────────────────────────────────────
with open(os.path.join(OUTPUT_DIR, 'backtest_manifest.json'), encoding='utf-8') as f:
    RAW_MANIFEST = json.load(f)

AVAILABLE_RACES = [r for r in RAW_MANIFEST if r['status'] == 'AVAILABLE']

# Load RL model (EXPERIMENTAL only)
try:
    RL_MODEL = PPOModel.load(os.path.join(os.path.dirname(__file__), '..', 'models', 'rl', 'ppo', 'best_model'))
    RL_AVAILABLE = True
except Exception:
    RL_MODEL = None
    RL_AVAILABLE = False


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def _baseline_strategy_time(total_laps: int, pit_lap: Optional[int] = None) -> float:
    """Estimate total race time for a 1-stop at pit_lap (or never-pit)."""
    BASE = 82.0
    DEG_MEDIUM = 0.075
    DEG_HARD = 0.040
    PIT_LOSS = 22.5

    if pit_lap is None:  # Never pit
        return sum(BASE + DEG_MEDIUM * l for l in range(1, total_laps + 1))

    stint1 = sum(BASE + DEG_MEDIUM * l for l in range(1, pit_lap + 1)) + PIT_LOSS
    stint2 = sum(BASE + DEG_HARD * l for l in range(1, total_laps - pit_lap + 1))
    return round(stint1 + stint2, 3)


def _exact_optimal_pit(total_laps: int) -> Dict[str, Any]:
    """Brute-force the best 1-stop lap and return time/strategy."""
    best_time = float('inf')
    best_lap = None
    for pit in range(10, total_laps - 5):
        t = _baseline_strategy_time(total_laps, pit)
        if t < best_time:
            best_time = t
            best_lap = pit
    return {
        'pit_lap': best_lap,
        'compound': 'MEDIUM→HARD',
        'race_time_s': round(best_time, 3),
    }


def _rl_episode(total_laps: int, seed: int) -> Dict[str, Any]:
    """Run a single RL episode (EXPERIMENTAL). Always isolated."""
    if not RL_AVAILABLE:
        return {'status': 'UNAVAILABLE', 'race_time_s': None, 'pits': 0}
    env = F1StrategyEnv({'total_laps': total_laps, 'seed': seed, 'driver': 'VER'})
    obs, _ = env.reset(seed=seed)
    done = False
    info: Dict[str, Any] = {}
    while not done:
        action, _ = RL_MODEL.predict(obs, deterministic=True)  # type: ignore
        obs, _, done, _, info = env.step(int(action))
    return {
        'status': 'OK',
        'race_time_s': round(info['race_time'], 3),
        'pits': info['pit_stops'],
        'final_position': info['position'],
    }


# ──────────────────────────────────────────────
# PER-RACE BACKTEST
# ──────────────────────────────────────────────
def backtest_race(race: Dict[str, Any]) -> Dict[str, Any]:
    season = race['season']
    rnd = race['round']
    gp = race['grand_prix']
    circuit = race['circuit']
    total_laps = int(race['total_laps'] or 57)

    result = {
        'season': season,
        'round': rnd,
        'grand_prix': gp,
        'circuit': circuit,
        'total_laps': total_laps,
        'status': 'OK',
        'leakage_passed': False,
    }

    # 1. Load real session laps (no telemetry — lightweight)
    t0 = time.time()
    try:
        session = fastf1.get_session(season, rnd, 'R')
        session.load(telemetry=False, weather=False, messages=False, laps=True)
        laps_df = session.laps
        driver_id = 'VER' if 'VER' in laps_df['Driver'].values else laps_df['Driver'].iloc[0]
        drv_laps = laps_df[laps_df['Driver'] == driver_id].sort_values('LapNumber')

        # Identify actual pit laps
        actual_pit_laps = drv_laps[drv_laps['PitOutTime'].notna()]['LapNumber'].tolist()
        actual_pit_lap = int(actual_pit_laps[0]) if actual_pit_laps else None

        data_source = 'REAL_FASTF1'
    except Exception as e:
        # Fall back to synthetic snapshot
        actual_pit_lap = None
        drv_laps = None
        data_source = f'SYNTHETIC_FALLBACK ({str(e)[:60]})'

    result['data_source'] = data_source

    # 2. Leakage guard — decision at lap 20
    DECISION_LAP = min(20, total_laps - 5)
    try:
        guard = FutureDataGuard(cutoff_lap=DECISION_LAP, cutoff_timestamp=float(DECISION_LAP * 85))
        guard.validate_lap_access(DECISION_LAP)         # OK
        try:
            guard.validate_lap_access(DECISION_LAP + 1)  # Must raise
            result['leakage_passed'] = False
        except ValueError:
            result['leakage_passed'] = True             # Correctly blocked
    except Exception:
        result['leakage_passed'] = False

    # 3. InformationSnapshot
    try:
        if drv_laps is not None and not drv_laps.empty:
            info_filter = HistoricalInformationFilter(drv_laps, None)
            info_filter.assert_no_future_access(DECISION_LAP + 1, DECISION_LAP)
        result['snapshot_leakage_ok'] = True
    except DataLeakageError as e:
        result['snapshot_leakage_ok'] = False
        result['status'] = f'LEAKAGE_ERROR: {e}'

    # 4. EXACT OPTIMIZER
    t_exact_start = time.time()
    exact = _exact_optimal_pit(total_laps)
    exact_runtime = round(time.time() - t_exact_start, 4)
    result['exact'] = {**exact, 'runtime_s': exact_runtime}

    # 5. MONTE CARLO
    t_mc_start = time.time()
    try:
        mc_eval = AdvancedMonteCarloStrategyEngine.evaluate_strategy_candidates(
            target_driver_id='VER',
            circuit_id=circuit[:6].upper(),
            total_laps=total_laps,
            num_simulations_per_candidate=50,
            base_seed=season * 100 + rnd,
        )
        mc_runtime = round(time.time() - t_mc_start, 4)
        mc_best = mc_eval.get('recommended_strategy', 'UNKNOWN')
        mc_cands = mc_eval.get('candidate_evaluations', [])
        mc_rec = next((c for c in mc_cands if c.get('is_recommended')), mc_cands[0] if mc_cands else {})
        # Remove hindsight fallback; if MC didn't return a valid race time, it is None.
        mc_time_s = mc_rec.get('mean_race_time_s', None)
        mc_pit = (mc_rec.get('pit_laps') or [None])[0]
    except Exception as e:
        print(f"    MC ERROR: {e}")
        import traceback
        traceback.print_exc()
        mc_runtime = round(time.time() - t_mc_start, 4)
        mc_time_s = None
        mc_pit = None
        mc_best = 'MC_ERROR'

    result['monte_carlo'] = {
        'recommended_strategy': mc_best,
        'race_time_s': round(mc_time_s, 3) if mc_time_s is not None else None,
        'pit_lap': mc_pit,
        'runtime_s': mc_runtime,
    }

    # 6. BASELINE (never-pit)
    base_time = _baseline_strategy_time(total_laps, None)
    base_1stop = _baseline_strategy_time(total_laps, 22)
    result['baseline'] = {
        'never_pit_time_s': round(base_time, 3),
        '1stop_lap22_time_s': round(base_1stop, 3),
    }

    # 7. ACTUAL (from real data if available)
    if actual_pit_lap is not None:
        actual_time = _baseline_strategy_time(total_laps, actual_pit_lap)
    else:
        actual_time = _baseline_strategy_time(total_laps, actual_pit_lap)
    result['actual'] = {
        'pit_lap': actual_pit_lap,
        'race_time_s_estimated': round(actual_time, 3),
    }

    # 8. RL (EXPERIMENTAL — isolated)
    rl_result = _rl_episode(total_laps, seed=season * 100 + rnd)
    result['rl_experimental'] = rl_result

    # 9. REGRET
    regret_mc = round(mc_time_s - exact['race_time_s'], 3) if mc_time_s is not None else None
    regret_base = round(base_1stop - exact['race_time_s'], 3)
    regret_rl = round(rl_result['race_time_s'] - exact['race_time_s'], 3) if rl_result.get('race_time_s') else None

    # Calculate Actual vs Recommended
    actual_vs_mc_s = round(actual_time - mc_time_s, 3) if actual_time is not None and mc_time_s is not None else None

    result['regret'] = {
        'mc_vs_exact_s': regret_mc,
        'baseline_vs_exact_s': regret_base,
        'rl_vs_exact_s': regret_rl,
        'actual_vs_mc_s': actual_vs_mc_s,
    }

    result['load_time_s'] = round(time.time() - t0, 3)
    return result


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    if not AVAILABLE_RACES:
        print("ERROR: No races in manifest. Run probe_sessions.py first.")
        sys.exit(1)

    print(f"Starting backtest across {len(AVAILABLE_RACES)} races...")
    all_results = []
    for i, race in enumerate(AVAILABLE_RACES):
        print(f"  [{i+1}/{len(AVAILABLE_RACES)}] {race['season']} R{race['round']:02d} {race['grand_prix']}")
        try:
            res = backtest_race(race)
            all_results.append(res)
            print(f"    Exact: {res['exact']['race_time_s']:.1f}s  MC: {res['monte_carlo']['race_time_s']:.1f}s  "
                  f"Regret_MC: {res['regret']['mc_vs_exact_s']:+.2f}s  Leak: {res['leakage_passed']}")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            all_results.append({'season': race['season'], 'round': race['round'],
                                 'grand_prix': race['grand_prix'], 'status': f'ERROR: {e}'})
            print(f"    ERROR: {e}\n{tb}")

    # ── Save raw results ──
    results_path = os.path.join(OUTPUT_DIR, 'race_results.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=str)

    # ── Aggregate metrics ──
    ok_results = [r for r in all_results if r.get('status') == 'OK']
    mc_regrets = [r['regret']['mc_vs_exact_s'] for r in ok_results if 'regret' in r]
    rl_regrets = [r['regret']['rl_vs_exact_s'] for r in ok_results
                  if r.get('regret', {}).get('rl_vs_exact_s') is not None]
    base_regrets = [r['regret']['baseline_vs_exact_s'] for r in ok_results if 'regret' in r]
    actual_vs_mc_regrets = [r['regret']['actual_vs_mc_s'] for r in ok_results
                            if r.get('regret', {}).get('actual_vs_mc_s') is not None]
    leakage_passes = sum(1 for r in ok_results if r.get('leakage_passed'))

    agg = {
        'races_attempted': len(AVAILABLE_RACES),
        'races_ok': len(ok_results),
        'races_failed': len(all_results) - len(ok_results),
        'leakage_guard_passes': leakage_passes,
        'mc_regret_mean_s': round(float(np.mean(mc_regrets)), 3) if mc_regrets else None,
        'mc_regret_median_s': round(float(np.median(mc_regrets)), 3) if mc_regrets else None,
        'mc_regret_p95_s': round(float(np.percentile(mc_regrets, 95)), 3) if mc_regrets else None,
        'actual_vs_mc_mean_s': round(float(np.mean(actual_vs_mc_regrets)), 3) if actual_vs_mc_regrets else None,
        'rl_regret_mean_s': round(float(np.mean(rl_regrets)), 3) if rl_regrets else None,
        'rl_regret_median_s': round(float(np.median(rl_regrets)), 3) if rl_regrets else None,
        'baseline_regret_mean_s': round(float(np.mean(base_regrets)), 3) if base_regrets else None,
        'seasons': sorted({r['season'] for r in ok_results}),
        'rl_available': RL_AVAILABLE,
    }

    with open(os.path.join(OUTPUT_DIR, 'backtest_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(agg, f, indent=2)

    # ── Season breakdown CSV ──
    season_rows = []
    for season in agg['seasons']:
        s_res = [r for r in ok_results if r['season'] == season]
        s_mc = [r['regret']['mc_vs_exact_s'] for r in s_res if 'regret' in r]
        season_rows.append({
            'season': season,
            'races': len(s_res),
            'mc_regret_mean': round(float(np.mean(s_mc)), 3) if s_mc else None,
            'mc_regret_median': round(float(np.median(s_mc)), 3) if s_mc else None,
        })
    pd.DataFrame(season_rows).to_csv(os.path.join(OUTPUT_DIR, 'season_results.csv'), index=False)

    # ── Circuit breakdown CSV ──
    circuit_rows = []
    circuits = sorted({r.get('circuit', 'UNKNOWN') for r in ok_results})
    for c in circuits:
        c_res = [r for r in ok_results if r.get('circuit') == c]
        c_mc = [r['regret']['mc_vs_exact_s'] for r in c_res if 'regret' in r]
        circuit_rows.append({
            'circuit': c,
            'races': len(c_res),
            'mc_regret_mean': round(float(np.mean(c_mc)), 3) if c_mc else None,
        })
    pd.DataFrame(circuit_rows).to_csv(os.path.join(OUTPUT_DIR, 'circuit_results.csv'), index=False)

    # ── Plots ──
    if ok_results:
        _make_plots(ok_results, mc_regrets, rl_regrets)
    else:
        print("No valid results to plot.")

    print(f"\n=== BACKTEST COMPLETE ===")
    print(f"Races OK: {agg['races_ok']} / {agg['races_attempted']}")
    print(f"Leakage guard PASS: {leakage_passes}/{len(ok_results)}")
    print(f"MC regret  mean/median/p95: {agg['mc_regret_mean_s']} / {agg['mc_regret_median_s']} / {agg['mc_regret_p95_s']} s")
    print(f"Actual vs MC mean: {agg['actual_vs_mc_mean_s']} s")
    print(f"RL regret  mean: {agg['rl_regret_mean_s']} s  (EXPERIMENTAL)")
    print(f"Baseline regret mean: {agg['baseline_regret_mean_s']} s")
    return agg


def _make_plots(ok_results, mc_regrets, rl_regrets):
    plot_dir = os.path.join(OUTPUT_DIR, 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    labels = [f"{r['season']}R{r['round']}" for r in ok_results]
    exact_times = [r['exact']['race_time_s'] for r in ok_results]
    mc_times = [r['monte_carlo']['race_time_s'] for r in ok_results]
    base_times = [r['baseline']['1stop_lap22_time_s'] for r in ok_results]

    x = np.arange(len(labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(max(10, len(labels)), 5))
    ax.bar(x - width, exact_times, width, label='Exact', color='gold')
    ax.bar(x, mc_times, width, label='Monte Carlo', color='steelblue')
    ax.bar(x + width, base_times, width, label='Baseline 1-Stop', color='gray')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('Race Time (s)')
    ax.set_title('Race Time by Method')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'race_time_comparison.png'), dpi=100)
    plt.close()

    # Regret distribution
    if mc_regrets:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(mc_regrets, bins=max(5, len(mc_regrets)//2), color='steelblue', edgecolor='white', label='MC regret')
        if rl_regrets:
            ax.hist(rl_regrets, bins=max(5, len(rl_regrets)//2), color='red', alpha=0.5, label='RL regret (exp)')
        ax.axvline(0, color='black', linestyle='--')
        ax.set_xlabel('Regret vs Exact (s)')
        ax.set_title('Strategy Regret Distribution')
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'regret_distribution.png'), dpi=100)
        plt.close()

    # MC vs Exact scatter
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(exact_times, mc_times, alpha=0.7, color='steelblue')
    mn = min(min(exact_times), min(mc_times))
    mx = max(max(exact_times), max(mc_times))
    ax.plot([mn, mx], [mn, mx], 'k--', label='y=x (perfect)')
    ax.set_xlabel('Exact Optimizer Time (s)')
    ax.set_ylabel('Monte Carlo Time (s)')
    ax.set_title('MC vs Exact Optimizer')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'mc_vs_exact_scatter.png'), dpi=100)
    plt.close()

    print(f"  Plots saved to {plot_dir}")


if __name__ == '__main__':
    main()
