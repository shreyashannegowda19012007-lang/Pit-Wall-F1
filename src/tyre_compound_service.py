"""
Tyre Compound Selection & Physical Compound Specification Service for Pitwall F1.
Maps nominal race weekend designations (SOFT, MEDIUM, HARD) to actual physical Pirelli
compounds (C1, C2, C3, C4, C5, C6) across seasons, providing physics parameters including
base grip offsets, thermal operating ranges, wear rates, and degradation curves.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional, Tuple, Any, List


@dataclass(frozen=True)
class PhysicalCompoundSpec:
    compound_code: str          # "C1", "C2", "C3", "C4", "C5", "C6", "INTERMEDIATE", "WET"
    nominal_hardness: str       # "HARDEST", "HARD", "MEDIUM", "SOFT", "SOFTEST", "INTERMEDIATE", "WET"
    base_grip_offset_s: float   # Lap pace delta relative to C3 reference (negative = faster grip)
    base_degradation_s_per_lap: float # Intrinsic wear rate on neutral 3/5 abrasion track
    optimal_temp_c: float       # Optimal bulk operating temperature
    temp_window_c: float        # Operating window +/- degrees Celsius
    cliff_lap_threshold: int    # Wear cliff lap where degradation goes nonlinear
    sliding_thermal_sensitivity: float # Sensitivity to sliding/overheating in dirty air / low grip


# Physical Pirelli dry slick compound range specifications
PHYSICAL_COMPOUND_SPECS: Dict[str, PhysicalCompoundSpec] = {
    "C1": PhysicalCompoundSpec(
        compound_code="C1",
        nominal_hardness="HARDEST",
        base_grip_offset_s=+1.10,     # Low initial grip (+1.1s vs C3)
        base_degradation_s_per_lap=0.038, # Very durable, low degradation
        optimal_temp_c=115.0,
        temp_window_c=25.0,
        cliff_lap_threshold=42,
        sliding_thermal_sensitivity=0.85 # Prone to sliding on smooth/low-energy circuits
    ),
    "C2": PhysicalCompoundSpec(
        compound_code="C2",
        nominal_hardness="HARD",
        base_grip_offset_s=+0.55,
        base_degradation_s_per_lap=0.065,
        optimal_temp_c=110.0,
        temp_window_c=20.0,
        cliff_lap_threshold=34,
        sliding_thermal_sensitivity=0.90
    ),
    "C3": PhysicalCompoundSpec(
        compound_code="C3",
        nominal_hardness="MEDIUM",
        base_grip_offset_s=0.00,      # Reference baseline
        base_degradation_s_per_lap=0.088,
        optimal_temp_c=105.0,
        temp_window_c=18.0,
        cliff_lap_threshold=28,
        sliding_thermal_sensitivity=1.00
    ),
    "C4": PhysicalCompoundSpec(
        compound_code="C4",
        nominal_hardness="SOFT",
        base_grip_offset_s=-0.50,
        base_degradation_s_per_lap=0.125,
        optimal_temp_c=100.0,
        temp_window_c=15.0,
        cliff_lap_threshold=22,
        sliding_thermal_sensitivity=1.15
    ),
    "C5": PhysicalCompoundSpec(
        compound_code="C5",
        nominal_hardness="SOFTEST",
        base_grip_offset_s=-0.95,
        base_degradation_s_per_lap=0.165,
        optimal_temp_c=95.0,
        temp_window_c=12.0,
        cliff_lap_threshold=16,
        sliding_thermal_sensitivity=1.35
    ),
    "C6": PhysicalCompoundSpec(
        compound_code="C6",
        nominal_hardness="ULTRA_SOFT",
        base_grip_offset_s=-1.30,
        base_degradation_s_per_lap=0.210,
        optimal_temp_c=90.0,
        temp_window_c=10.0,
        cliff_lap_threshold=12,
        sliding_thermal_sensitivity=1.50
    ),
    "INTERMEDIATE": PhysicalCompoundSpec(
        compound_code="INTERMEDIATE",
        nominal_hardness="INTERMEDIATE",
        base_grip_offset_s=+4.00,
        base_degradation_s_per_lap=0.100,
        optimal_temp_c=80.0,
        temp_window_c=25.0,
        cliff_lap_threshold=30,
        sliding_thermal_sensitivity=1.80
    ),
    "WET": PhysicalCompoundSpec(
        compound_code="WET",
        nominal_hardness="WET",
        base_grip_offset_s=+8.00,
        base_degradation_s_per_lap=0.080,
        optimal_temp_c=70.0,
        temp_window_c=30.0,
        cliff_lap_threshold=35,
        sliding_thermal_sensitivity=2.00
    )
}


@dataclass(frozen=True)
class EventCompoundNomination:
    season: int
    circuit_key: str
    hard_physical: str    # e.g. "C1"
    medium_physical: str  # e.g. "C2"
    soft_physical: str    # e.g. "C3"
    provenance: str       # "PIRELLI_OFFICIAL_NOMINATION", "CALIBRATED_ESTIMATE", "UNKNOWN_FALLBACK"


# Authoritative Pirelli season nominations database (Hard, Medium, Soft)
NOMINATIONS_DATABASE: Dict[Tuple[int, str], EventCompoundNomination] = {
    # 2025 Season
    (2025, "SPAIN"): EventCompoundNomination(2025, "SPAIN", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "MONACO"): EventCompoundNomination(2025, "MONACO", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "SILVERSTONE"): EventCompoundNomination(2025, "SILVERSTONE", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "BAHRAIN"): EventCompoundNomination(2025, "BAHRAIN", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "MONZA"): EventCompoundNomination(2025, "MONZA", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "SPA"): EventCompoundNomination(2025, "SPA", "C2", "C3", "C4", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "HUNGARY"): EventCompoundNomination(2025, "HUNGARY", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "AUSTRIA"): EventCompoundNomination(2025, "AUSTRIA", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "ZANDVOORT"): EventCompoundNomination(2025, "ZANDVOORT", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "SINGAPORE"): EventCompoundNomination(2025, "SINGAPORE", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "SUZUKA"): EventCompoundNomination(2025, "SUZUKA", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "COTA"): EventCompoundNomination(2025, "COTA", "C2", "C3", "C4", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "MEXICO"): EventCompoundNomination(2025, "MEXICO", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "INTERLAGOS"): EventCompoundNomination(2025, "INTERLAGOS", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "LAS_VEGAS"): EventCompoundNomination(2025, "LAS_VEGAS", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "QATAR"): EventCompoundNomination(2025, "QATAR", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "ABU_DHABI"): EventCompoundNomination(2025, "ABU_DHABI", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "AUSTRALIA"): EventCompoundNomination(2025, "AUSTRALIA", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "CHINA"): EventCompoundNomination(2025, "CHINA", "C2", "C3", "C4", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "MIAMI"): EventCompoundNomination(2025, "MIAMI", "C2", "C3", "C4", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "IMOLA"): EventCompoundNomination(2025, "IMOLA", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "CANADA"): EventCompoundNomination(2025, "CANADA", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "BAKU"): EventCompoundNomination(2025, "BAKU", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2025, "JEDDAH"): EventCompoundNomination(2025, "JEDDAH", "C2", "C3", "C4", "PIRELLI_OFFICIAL_NOMINATION"),

    # 2024 Season
    (2024, "SPAIN"): EventCompoundNomination(2024, "SPAIN", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "MONACO"): EventCompoundNomination(2024, "MONACO", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "SILVERSTONE"): EventCompoundNomination(2024, "SILVERSTONE", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "BAHRAIN"): EventCompoundNomination(2024, "BAHRAIN", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "MONZA"): EventCompoundNomination(2024, "MONZA", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "SPA"): EventCompoundNomination(2024, "SPA", "C2", "C3", "C4", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "HUNGARY"): EventCompoundNomination(2024, "HUNGARY", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "AUSTRIA"): EventCompoundNomination(2024, "AUSTRIA", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "ZANDVOORT"): EventCompoundNomination(2024, "ZANDVOORT", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "SINGAPORE"): EventCompoundNomination(2024, "SINGAPORE", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "SUZUKA"): EventCompoundNomination(2024, "SUZUKA", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "COTA"): EventCompoundNomination(2024, "COTA", "C2", "C3", "C4", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "MEXICO"): EventCompoundNomination(2024, "MEXICO", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "INTERLAGOS"): EventCompoundNomination(2024, "INTERLAGOS", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "LAS_VEGAS"): EventCompoundNomination(2024, "LAS_VEGAS", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "QATAR"): EventCompoundNomination(2024, "QATAR", "C1", "C2", "C3", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "ABU_DHABI"): EventCompoundNomination(2024, "ABU_DHABI", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "AUSTRALIA"): EventCompoundNomination(2024, "AUSTRALIA", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "CHINA"): EventCompoundNomination(2024, "CHINA", "C2", "C3", "C4", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "MIAMI"): EventCompoundNomination(2024, "MIAMI", "C2", "C3", "C4", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "IMOLA"): EventCompoundNomination(2024, "IMOLA", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "CANADA"): EventCompoundNomination(2024, "CANADA", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "BAKU"): EventCompoundNomination(2024, "BAKU", "C3", "C4", "C5", "PIRELLI_OFFICIAL_NOMINATION"),
    (2024, "JEDDAH"): EventCompoundNomination(2024, "JEDDAH", "C2", "C3", "C4", "PIRELLI_OFFICIAL_NOMINATION"),

    # 2026 Regulations Projections
    (2026, "SPAIN"): EventCompoundNomination(2026, "SPAIN", "C1", "C2", "C3", "CALIBRATED_ESTIMATE"),
    (2026, "MONACO"): EventCompoundNomination(2026, "MONACO", "C4", "C5", "C6", "CALIBRATED_ESTIMATE"),
    (2026, "SILVERSTONE"): EventCompoundNomination(2026, "SILVERSTONE", "C1", "C2", "C3", "CALIBRATED_ESTIMATE"),
}


class TyreCompoundService:
    """Historical tyre compound selection and physics resolution engine."""

    @classmethod
    def resolve_event_nomination(cls, season: int, circuit_key: str) -> EventCompoundNomination:
        """
        Resolves the actual physical compounds (Hard, Medium, Soft) for a given season and circuit.
        Falls back to circuit profile characteristics with transparent provenance when missing.
        """
        key = (season, circuit_key)
        if key in NOMINATIONS_DATABASE:
            return NOMINATIONS_DATABASE[key]

        # Check prior year for the same circuit
        for prev_season in (2025, 2024, 2023):
            if (prev_season, circuit_key) in NOMINATIONS_DATABASE:
                base = NOMINATIONS_DATABASE[(prev_season, circuit_key)]
                return EventCompoundNomination(
                    season=season,
                    circuit_key=circuit_key,
                    hard_physical=base.hard_physical,
                    medium_physical=base.medium_physical,
                    soft_physical=base.soft_physical,
                    provenance=f"CARRIED_FROM_{prev_season}_HISTORICAL"
                )

        # Dynamic fallback based on circuit stress
        # High stress circuits (Barcelona, Silverstone, Suzuka) get C1-C2-C3
        # Street circuits (Monaco, Singapore, Baku) get C3-C4-C5
        # Standard circuits get C2-C3-C4
        from circuit_database import CircuitDatabase
        prof = CircuitDatabase.get_circuit_profile(circuit_key)
        if prof.tyre_stress_rating >= 4:
            return EventCompoundNomination(season, circuit_key, "C1", "C2", "C3", "CALIBRATED_STRESS_INFERRED")
        elif prof.tyre_stress_rating <= 2:
            return EventCompoundNomination(season, circuit_key, "C3", "C4", "C5", "CALIBRATED_STRESS_INFERRED")
        else:
            return EventCompoundNomination(season, circuit_key, "C2", "C3", "C4", "CALIBRATED_STRESS_INFERRED")

    @classmethod
    def get_physical_compound_for_nominal(cls, nominal: str, season: int, circuit_key: str) -> Tuple[str, PhysicalCompoundSpec, str]:
        """
        Maps a nominal compound ("SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET")
        to its physical specification (e.g. C1, C2, C3...) and reports provenance.
        """
        norm = nominal.upper().strip()
        if norm in ("INTERMEDIATE", "INTER", "I"):
            return "INTERMEDIATE", PHYSICAL_COMPOUND_SPECS["INTERMEDIATE"], "REGULATION_STANDARD"
        if norm in ("WET", "FULL_WET", "W"):
            return "WET", PHYSICAL_COMPOUND_SPECS["WET"], "REGULATION_STANDARD"

        nom = cls.resolve_event_nomination(season, circuit_key)
        if norm == "HARD":
            code = nom.hard_physical
        elif norm == "MEDIUM":
            code = nom.medium_physical
        elif norm == "SOFT":
            code = nom.soft_physical
        else:
            code = "C3" # fallback

        spec = PHYSICAL_COMPOUND_SPECS.get(code, PHYSICAL_COMPOUND_SPECS["C3"])
        return code, spec, nom.provenance

    @classmethod
    def get_compound_pace_and_degradation(
        cls,
        nominal_compound: str,
        season: int,
        circuit_key: str,
        track_temp_c: Optional[float] = None,
        tyre_stress_rating: Optional[int] = None,
        asphalt_abrasion_rating: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Computes calibrated pace offset and degradation rate for a nominal compound
        at a specific circuit, season, and track temperature.
        """
        from circuit_database import CircuitDatabase
        prof = CircuitDatabase.get_circuit_profile(circuit_key)

        code, spec, prov = cls.get_physical_compound_for_nominal(nominal_compound, season, circuit_key)

        temp = track_temp_c if track_temp_c is not None else prof.typical_track_temp_c
        stress = tyre_stress_rating if tyre_stress_rating is not None else prof.tyre_stress_rating
        abrasion = asphalt_abrasion_rating if asphalt_abrasion_rating is not None else prof.asphalt_abrasion_rating

        # Surface stress multiplier: neutral is 3/5. Each point adds +/- 18% wear
        stress_mult = 1.0 + (stress - 3) * 0.18 + (abrasion - 3) * 0.15

        # Thermal deviation multiplier: operating above optimal accelerates thermal deg
        temp_delta = temp - spec.optimal_temp_c
        thermal_mult = 1.0 + max(0.0, temp_delta) * 0.012

        calibrated_deg = spec.base_degradation_s_per_lap * stress_mult * thermal_mult

        # Special Barcelona 2025 / High-Stress C1 behavior:
        # If Hard is C1 on a high-energy track with low track grip, low grip causes sliding and surface overheating
        sliding_penalty = 0.0
        if code == "C1" and stress >= 4:
            # Low mechanical grip on C1 increases wheelspin/sliding, penalizing pace by an additional 0.35s
            sliding_penalty = 0.35

        effective_pace = spec.base_grip_offset_s + sliding_penalty

        return {
            "nominal_compound": nominal_compound.upper(),
            "physical_compound": code,
            "provenance": prov,
            "base_pace_delta_s": round(effective_pace, 3),
            "calibrated_degradation_s_per_lap": round(calibrated_deg, 4),
            "cliff_lap": spec.cliff_lap_threshold,
            "optimal_temp_c": spec.optimal_temp_c,
            "current_track_temp_c": temp,
            "stress_multiplier": round(stress_mult, 3)
        }
