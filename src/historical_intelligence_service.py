"""
Historical Intelligence, Era Comparisons & Championship What-If Engine.
Provides regulation-era technical comparisons (Ground Effect vs Hybrid vs V8),
teammate head-to-head career databases, and mathematical championship points calculators.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from src.data_provenance import DataClassification, ProvenanceRecord


@dataclass
class RegulationEraSummary:
    era_id: str
    era_name: str
    season_range: str
    engine_architecture: str
    displacement_litres: float
    max_rpm: int
    hybrid_system: str
    aerodynamic_concept: str
    minimum_weight_kg: float
    tyre_specification: str
    overtaking_delta_characteristics: str
    fuel_regulation: str


@dataclass
class TeammateHeadToHead:
    team_name: str
    season: int
    driver_1_code: str
    driver_2_code: str
    qualifying_head_to_head: str       # e.g., "16 - 8"
    race_head_to_head: str             # e.g., "18 - 6"
    points_driver_1: float
    points_driver_2: float
    podiums_driver_1: int
    podiums_driver_2: int
    wins_driver_1: int
    wins_driver_2: int
    avg_quali_delta_s: float           # Negative means driver 1 faster


@dataclass
class ChampionshipWhatIfOutcome:
    driver_code: str
    team_name: str
    current_points: float
    projected_points_finish_p1: float
    projected_points_finish_p2: float
    projected_points_finish_p3: float
    mathematical_title_clinch_possible: bool
    points_needed_to_clinch: float


class HistoricalIntelligenceService:
    """Authoritative Historical Intelligence & Regulation Era Engine."""

    REGULATION_ERAS: List[RegulationEraSummary] = [
        RegulationEraSummary(
            era_id="GROUND_EFFECT_2022_2025",
            era_name="Ground Effect Venturi Floor Era",
            season_range="2022 - 2025",
            engine_architecture="1.6L 90° V6 Single Turbocharged",
            displacement_litres=1.6,
            max_rpm=15000,
            hybrid_system="120 kW MGU-K + MGU-H (Unlimited Recuperation)",
            aerodynamic_concept="Underfloor 3D Venturi tunnels with floor edge winglets and simplified front/beam wings to minimize dirty air wake.",
            minimum_weight_kg=798.0,
            tyre_specification="18-inch low-profile Pirelli with wheel covers",
            overtaking_delta_characteristics="Close following capability increased by ~40% at 20m distance; high sensitivity to ride-height porpoising.",
            fuel_regulation="100 kg/h max flow rate; E10 sustainable fuel blend."
        ),
        RegulationEraSummary(
            era_id="TURBO_HYBRID_2014_2021",
            era_name="V6 Turbo-Hybrid Bargeboard Era",
            season_range="2014 - 2021",
            engine_architecture="1.6L 90° V6 Single Turbocharged",
            displacement_litres=1.6,
            max_rpm=15000,
            hybrid_system="120 kW MGU-K (2 MJ/lap deploy) + MGU-H",
            aerodynamic_concept="Intricate multi-element aerodynamic bargeboards, front wing Y250 vortex generators, high-rake floors.",
            minimum_weight_kg=752.0,
            tyre_specification="13-inch high-profile Pirelli",
            overtaking_delta_characteristics="High downforce but severe wake dirty air loss (~45% downforce loss at 20m behind rival car).",
            fuel_regulation="105 kg race fuel allowance; 100 kg/h ultrasonic fuel flow meter limit."
        ),
        RegulationEraSummary(
            era_id="V8_NATURALLY_ASPIRATED_2006_2013",
            era_name="2.4L V8 Naturally Aspirated & KERS Era",
            season_range="2006 - 2013",
            engine_architecture="2.4L 90° V8 Naturally Aspirated",
            displacement_litres=2.4,
            max_rpm=18000,
            hybrid_system="60 kW KERS Flywheel/Battery (400 kJ / 6.6s per lap from 2009)",
            aerodynamic_concept="High-downforce stepped floors, blown diffusers (exhaust gas blowing floor), beam wings.",
            minimum_weight_kg=642.0,
            tyre_specification="13-inch Bridgestone (grooved 2006-2008, slick 2009-2010), Pirelli (2011-2013)",
            overtaking_delta_characteristics="High mechanical grip and light agile chassis; DRS introduced in 2011 to aid overtaking.",
            fuel_regulation="In-race refuelling banned from 2010; no fuel mass flow restrictions."
        ),
        RegulationEraSummary(
            era_id="V10_ERA_1995_2005",
            era_name="3.0L V10 High-Revs Golden Era",
            season_range="1995 - 2005",
            engine_architecture="3.0L 72°-90° V10 Naturally Aspirated",
            displacement_litres=3.0,
            max_rpm=19500,
            hybrid_system="None (Pure Internal Combustion)",
            aerodynamic_concept="Unrestricted aerodynamic winglets, top-body flip-ups, stepped flat wooden plank floors.",
            minimum_weight_kg=605.0,
            tyre_specification="13-inch grooved tyres (Bridgestone vs Michelin tyre war)",
            overtaking_delta_characteristics="Ultra-lightweight ~950+ hp rockets; strategic refueling stops dictated race outcome.",
            fuel_regulation="In-race refuelling permitted with 12.1 litres/second high-pressure rig."
        )
    ]

    TEAMMATE_RECORDS: List[TeammateHeadToHead] = [
        TeammateHeadToHead("Red Bull Racing", 2024, "VER", "PER", "22 - 2", "20 - 4", 437.0, 152.0, 14, 4, 9, 0, -0.420),
        TeammateHeadToHead("McLaren", 2024, "NOR", "PIA", "18 - 6", "15 - 9", 374.0, 292.0, 12, 7, 4, 2, -0.185),
        TeammateHeadToHead("Ferrari", 2024, "LEC", "SAI", "15 - 9", "14 - 10", 356.0, 290.0, 11, 7, 3, 2, -0.110),
        TeammateHeadToHead("Mercedes", 2024, "RUS", "HAM", "16 - 8", "13 - 11", 245.0, 223.0, 4, 5, 2, 2, -0.095)
    ]

    @classmethod
    def get_eras(cls) -> List[Dict[str, Any]]:
        return [asdict(e) for e in cls.REGULATION_ERAS]

    @classmethod
    def get_teammate_head_to_head(cls, season: int = 2024) -> List[Dict[str, Any]]:
        records = [r for r in cls.TEAMMATE_RECORDS if r.season == season]
        return [asdict(r) for r in (records if records else cls.TEAMMATE_RECORDS)]

    @classmethod
    def calculate_championship_what_if(cls, session_id: str = "S-2024-SPAIN") -> List[Dict[str, Any]]:
        """
        Calculates mathematical title permutations and point scenarios.
        """
        from src.standings_service import StandingsService
        res = StandingsService.get_driver_standings(2024)
        standings = res.get("standings", [])

        if not standings:
            return []

        leader_pts = float(standings[0].get("points", 437.0))
        outcomes: List[ChampionshipWhatIfOutcome] = []

        for item in standings[:10]:
            code = item.get("driver_code", "DRV")
            team = item.get("team_name", "Team")
            pts = float(item.get("points", 0.0))

            # F1 points system: P1 = 25, P2 = 18, P3 = 15
            p1_pts = pts + 25.0
            p2_pts = pts + 18.0
            p3_pts = pts + 15.0

            # Mathematical clinch check
            can_clinch = (code == standings[0].get("driver_code")) and (leader_pts - float(standings[1].get("points", 0.0)) > 60.0)
            needed = max(0.0, leader_pts - pts)

            outcomes.append(ChampionshipWhatIfOutcome(
                driver_code=code,
                team_name=team,
                current_points=pts,
                projected_points_finish_p1=p1_pts,
                projected_points_finish_p2=p2_pts,
                projected_points_finish_p3=p3_pts,
                mathematical_title_clinch_possible=can_clinch,
                points_needed_to_clinch=round(needed, 1)
            ))

        return [asdict(o) for o in outcomes]
