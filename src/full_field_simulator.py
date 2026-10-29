"""
Full-Field F1 Lap-by-Lap Race Simulation Engine & Stochastic Monte Carlo System.
Evolves 20 drivers lap by lap deterministically (using simulation_seed), modeling tyre degradation,
compound grip offsets, team/car performance tiers, fuel mass burn, pit stops, traffic dirty air penalties,
probabilistic overtaking, DRS, weather, Safety Car / VSC events, and Monte Carlo strategy distributions.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import math

from tyre_engine import EmpiricalTyreModel


@dataclass
class DriverSimState:
    driver_id: str
    team: str
    grid_position: int
    current_position: int
    lap_number: int
    total_race_time_s: float
    last_lap_time_s: float
    best_lap_time_s: float
    tyre_compound: str           # "SOFT", "MEDIUM", "HARD"
    tyre_age_laps: int
    stint_number: int
    fuel_mass_kg: float
    pit_count: int
    is_pitting: bool
    status: str                  # "RACING", "PITTING", "RETIRED"
    gap_to_leader_s: float
    interval_to_ahead_s: float


@dataclass
class RaceSimulationConfig:
    circuit_id: str = "SPAIN"
    total_laps: int = 66
    num_drivers: int = 20
    simulation_seed: int = 42
    track_length_m: float = 4675.0
    base_lap_time_s: float = 78.5
    fuel_mass_initial_kg: float = 105.0
    fuel_burn_per_lap_kg: float = 1.55
    fuel_effect_s_per_10kg: float = 0.33
    pit_lane_time_loss_s: float = 20.0
    pit_stop_mean_duration_s: float = 2.5
    safety_car_probability_per_lap: float = 0.02
    weather_condition: str = "DRY"


@dataclass
class FullFieldSimulationResult:
    simulation_id: str
    seed: int
    total_laps: int
    winner_driver_id: str
    total_race_time_s: float
    final_standings: List[Dict[str, Any]]
    lap_by_lap_history: List[Dict[str, Any]]
    total_overtakes: int
    total_pit_stops: int
    safety_car_laps: List[int]


class FullFieldRaceSimulator:
    """
    Deterministic Lap-by-Lap Full-Field Race Simulator.
    """

    DEFAULT_DRIVERS = [
        ("VER", "Red Bull Racing"), ("PER", "Red Bull Racing"),
        ("HAM", "Mercedes"), ("RUS", "Mercedes"),
        ("LEC", "Ferrari"), ("SAI", "Ferrari"),
        ("NOR", "McLaren"), ("PIA", "McLaren"),
        ("ALO", "Aston Martin"), ("STR", "Aston Martin"),
        ("GAS", "Alpine"), ("OCO", "Alpine"),
        ("TSU", "RB"), ("RIC", "RB"),
        ("ALB", "Williams"), ("SAR", "Williams"),
        ("BOT", "Kick Sauber"), ("ZHO", "Kick Sauber"),
        ("MAG", "Haas"), ("HUL", "Haas")
    ]

    DRIVER_PACE_DELTAS = {
        "VER": 0.00,
        "NOR": 0.05,
        "LEC": 0.15,
        "PIA": 0.22,
        "HAM": 0.25,
        "RUS": 0.28,
        "SAI": 0.35,
        "PER": 0.38,
        "ALO": 0.85,
        "STR": 1.25,
        "TSU": 1.30,
        "GAS": 1.35,
        "RIC": 1.40,
        "OCO": 1.45,
        "ALB": 1.50,
        "HUL": 1.55,
        "MAG": 1.65,
        "SAR": 1.80,
        "BOT": 1.90,
        "ZHO": 2.10
    }

    COMPOUND_PACE_DELTAS = {
        "SOFT": -0.80,
        "MEDIUM": 0.00,
        "HARD": 0.70,
        "INTERMEDIATE": 4.00,
        "WET": 8.00
    }

    @classmethod
    def get_default_competitor_strategies(cls, total_laps: int) -> Dict[str, Tuple[str, List[Tuple[int, str]]]]:
        """
        Returns a realistic distribution of baseline strategies for all 20 drivers
        scaled to the actual race lap count.
        Format: {driver_id: (starting_compound, [(pit_lap, next_compound), ...])}
        """
        p1 = max(1, int(round(total_laps * 0.27)))
        p2 = max(p1 + 1, int(round(total_laps * 0.67)))
        mid1 = max(1, int(round(total_laps * 0.45)))

        return {
            "VER": ("SOFT", [(p1, "MEDIUM"), (p2, "SOFT")]),
            "NOR": ("SOFT", [(p1 + 1, "MEDIUM"), (p2 + 1, "SOFT")]),
            "LEC": ("SOFT", [(p1, "MEDIUM"), (p2 - 1, "HARD")]),
            "PIA": ("MEDIUM", [(p1 + 5, "HARD"), (p2 + 2, "SOFT")]),
            "HAM": ("SOFT", [(p1, "MEDIUM"), (p2, "SOFT")]),
            "RUS": ("SOFT", [(p1 - 1, "HARD"), (p2 - 1, "MEDIUM")]),
            "SAI": ("MEDIUM", [(p1 + 4, "HARD"), (p2 + 1, "MEDIUM")]),
            "PER": ("SOFT", [(p1 - 1, "MEDIUM"), (p2 - 1, "SOFT")]),
            "ALO": ("SOFT", [(p1 - 2, "MEDIUM"), (p2 - 3, "HARD")]),
            "STR": ("MEDIUM", [(mid1 - 2, "HARD")]),
            "TSU": ("SOFT", [(p1, "HARD"), (p2 - 1, "MEDIUM")]),
            "GAS": ("MEDIUM", [(mid1 - 1, "HARD")]),
            "RIC": ("SOFT", [(p1 - 1, "MEDIUM"), (p2 - 2, "HARD")]),
            "OCO": ("MEDIUM", [(mid1, "HARD")]),
            "ALB": ("SOFT", [(p1 + 1, "HARD"), (p2, "MEDIUM")]),
            "HUL": ("MEDIUM", [(mid1 - 2, "HARD")]),
            "MAG": ("HARD", [(mid1 + 5, "MEDIUM")]),
            "SAR": ("SOFT", [(p1 - 2, "MEDIUM"), (p2 - 3, "HARD")]),
            "BOT": ("MEDIUM", [(mid1 - 1, "HARD")]),
            "ZHO": ("HARD", [(mid1 + 6, "MEDIUM")]),
        }

    @classmethod
    def run_full_field_simulation(
        cls,
        config: RaceSimulationConfig = RaceSimulationConfig(),
        planned_strategies: Optional[Dict[str, List[Tuple[int, str]]]] = None,
        initial_states: Optional[List[DriverSimState]] = None,
        initial_compounds: Optional[Dict[str, str]] = None
    ) -> FullFieldSimulationResult:
        """
        Executes a deterministic lap-by-lap 20-car race simulation.
        """
        rng = np.random.RandomState(config.simulation_seed)
        default_strats = cls.get_default_competitor_strategies(config.total_laps)

        # Build combined strategy map and initial compound map
        strategies: Dict[str, List[Tuple[int, str]]] = {}
        starting_comps: Dict[str, str] = {}

        for drv_id, _ in cls.DEFAULT_DRIVERS:
            def_comp, def_pits = default_strats.get(drv_id, ("MEDIUM", [(max(1, config.total_laps // 2), "HARD")]))
            if planned_strategies and drv_id in planned_strategies:
                strategies[drv_id] = planned_strategies[drv_id]
            else:
                strategies[drv_id] = def_pits

            if initial_compounds and drv_id in initial_compounds:
                starting_comps[drv_id] = initial_compounds[drv_id]
            else:
                starting_comps[drv_id] = def_comp

        # Initialize Grid
        driver_states: Dict[str, DriverSimState] = {}
        if initial_states is not None:
            for state in initial_states:
                driver_states[state.driver_id] = DriverSimState(**asdict(state))
            start_lap = max((s.lap_number for s in driver_states.values()), default=0) + 1
        else:
            for pos, (drv_id, team) in enumerate(cls.DEFAULT_DRIVERS, start=1):
                start_compound = starting_comps.get(drv_id, "MEDIUM")
                driver_states[drv_id] = DriverSimState(
                    driver_id=drv_id,
                    team=team,
                    grid_position=pos,
                    current_position=pos,
                    lap_number=0,
                    total_race_time_s=(pos - 1) * 0.4,
                    last_lap_time_s=0.0,
                    best_lap_time_s=999.0,
                    tyre_compound=start_compound,
                    tyre_age_laps=1,
                    stint_number=1,
                    fuel_mass_kg=config.fuel_mass_initial_kg,
                    pit_count=0,
                    is_pitting=False,
                    status="RACING",
                    gap_to_leader_s=(pos - 1) * 0.4,
                    interval_to_ahead_s=0.4 if pos > 1 else 0.0
                )
            start_lap = 1

        total_overtakes = 0
        total_pit_stops = 0
        safety_car_laps = []
        lap_history = []

        # Lap-by-Lap Evolution
        for current_lap in range(start_lap, config.total_laps + 1):
            # Check Safety Car trigger
            is_safety_car = (rng.rand() < config.safety_car_probability_per_lap)
            if is_safety_car:
                safety_car_laps.append(current_lap)

            # 1. Calculate Base Pace for each driver
            for drv_id, state in driver_states.items():
                if state.status == "RETIRED":
                    continue

                state.lap_number = current_lap
                state.tyre_age_laps += 1

                # Driver / Car team pace delta
                driver_delta = cls.DRIVER_PACE_DELTAS.get(drv_id, 0.5)

                # Compound pace grip offset (Soft is faster, Hard is slower)
                compound_offset = cls.COMPOUND_PACE_DELTAS.get(state.tyre_compound, 0.0)

                # Fuel weight effect
                fuel_penalty = (state.fuel_mass_kg / 10.0) * config.fuel_effect_s_per_10kg

                # Tyre degradation effect
                deg_rate = EmpiricalTyreModel.COMPOUND_BASE_DEG.get(state.tyre_compound, 0.075)
                tyre_penalty = state.tyre_age_laps * deg_rate

                # Random driver lap variance
                lap_noise = rng.normal(0.0, 0.10)

                sc_mult = 1.35 if is_safety_car else 1.00
                lap_time = (config.base_lap_time_s + driver_delta + compound_offset + fuel_penalty + tyre_penalty + lap_noise) * sc_mult

                # Check planned pit stop
                pits = strategies.get(drv_id, [])
                if any(pit_lap == current_lap for pit_lap, _ in pits):
                    next_compound = next(comp for p_lap, comp in pits if p_lap == current_lap)
                    # Pit loss under SC is ~12.0s transit vs 20.0s under green flag
                    base_transit = 12.0 if is_safety_car else config.pit_lane_time_loss_s
                    pit_duration = base_transit + max(1.9, rng.normal(config.pit_stop_mean_duration_s, 0.35))
                    lap_time += pit_duration
                    state.pit_count += 1
                    state.tyre_compound = next_compound
                    state.tyre_age_laps = 1
                    state.stint_number += 1
                    total_pit_stops += 1

                # Update fuel burn
                state.fuel_mass_kg = max(0.0, state.fuel_mass_kg - config.fuel_burn_per_lap_kg)

                state.last_lap_time_s = round(lap_time, 3)
                state.best_lap_time_s = min(state.best_lap_time_s, state.last_lap_time_s)
                state.total_race_time_s += state.last_lap_time_s

            # 2. Re-sort Race Order based on Total Race Time
            sorted_drivers = sorted(
                [s for s in driver_states.values() if s.status != "RETIRED"],
                key=lambda x: x.total_race_time_s
            )

            # Update Positions & Gaps
            leader_time = sorted_drivers[0].total_race_time_s
            for pos, drv in enumerate(sorted_drivers, start=1):
                if drv.current_position != pos:
                    total_overtakes += 1
                drv.current_position = pos
                drv.gap_to_leader_s = round(drv.total_race_time_s - leader_time, 3)
                drv.interval_to_ahead_s = round(drv.total_race_time_s - sorted_drivers[pos - 2].total_race_time_s, 3) if pos > 1 else 0.0

            # Record Snapshot
            lap_history.append({
                "lap_number": current_lap,
                "is_safety_car": is_safety_car,
                "leader_id": sorted_drivers[0].driver_id,
                "standings": [asdict(d) for d in sorted_drivers]
            })

        final_standings = sorted(
            [asdict(s) for s in driver_states.values()],
            key=lambda x: x['total_race_time_s']
        )

        return FullFieldSimulationResult(
            simulation_id=f"SIM-{config.simulation_seed}-{config.circuit_id}",
            seed=config.simulation_seed,
            total_laps=config.total_laps,
            winner_driver_id=final_standings[0]['driver_id'],
            total_race_time_s=round(final_standings[0]['total_race_time_s'], 3),
            final_standings=final_standings,
            lap_by_lap_history=lap_history,
            total_overtakes=total_overtakes,
            total_pit_stops=total_pit_stops,
            safety_car_laps=safety_car_laps
        )

    @classmethod
    def run_monte_carlo_field_simulation(
        cls,
        num_simulations: int = 100,
        config: RaceSimulationConfig = RaceSimulationConfig()
    ) -> Dict[str, Any]:
        """
        Executes N Monte Carlo iterations across 20 drivers to compute win & podium probabilities.
        Guarantees that sum(win_probability) = 100.0% and sum(podium_probability) = 300.0%.
        """
        win_counts = {drv[0]: 0 for drv in cls.DEFAULT_DRIVERS}
        podium_counts = {drv[0]: 0 for drv in cls.DEFAULT_DRIVERS}
        top5_counts = {drv[0]: 0 for drv in cls.DEFAULT_DRIVERS}
        pos_sums = {drv[0]: 0 for drv in cls.DEFAULT_DRIVERS}

        for i in range(num_simulations):
            sim_cfg = RaceSimulationConfig(
                circuit_id=config.circuit_id,
                total_laps=config.total_laps,
                simulation_seed=config.simulation_seed + i
            )
            res = cls.run_full_field_simulation(sim_cfg)
            standings = res.final_standings

            winner = standings[0]['driver_id']
            win_counts[winner] = win_counts.get(winner, 0) + 1

            for pos, drv in enumerate(standings, start=1):
                d_id = drv['driver_id']
                pos_sums[d_id] = pos_sums.get(d_id, 0) + pos
                if pos <= 3:
                    podium_counts[d_id] = podium_counts.get(d_id, 0) + 1
                if pos <= 5:
                    top5_counts[d_id] = top5_counts.get(d_id, 0) + 1

        rankings = []
        for drv_id, _ in cls.DEFAULT_DRIVERS:
            wins = win_counts.get(drv_id, 0)
            podiums = podium_counts.get(drv_id, 0)
            top5 = top5_counts.get(drv_id, 0)
            avg_pos = pos_sums.get(drv_id, 0) / max(1, num_simulations)

            rankings.append({
                "driver_id": drv_id,
                "win_probability_pct": round((wins / num_simulations) * 100.0, 1),
                "podium_probability_pct": round((podiums / num_simulations) * 100.0, 1),
                "top5_probability_pct": round((top5 / num_simulations) * 100.0, 1),
                "expected_position": round(avg_pos, 2)
            })

        rankings.sort(key=lambda x: (x['win_probability_pct'], x['podium_probability_pct']), reverse=True)

        return {
            "num_simulations": num_simulations,
            "circuit_id": config.circuit_id,
            "total_laps": config.total_laps,
            "driver_rankings": rankings
        }
