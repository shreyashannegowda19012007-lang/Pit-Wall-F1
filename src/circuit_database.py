"""
Circuit & Event Engineering Database for Pitwall F1.
Provides canonical circuit dimensions, lap counts, pit-lane transit times,
surface abrasiveness, tyre stress ratings, and overtaking difficulty indices
for all contemporary and historical Formula One circuits.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional, Any, List


@dataclass(frozen=True)
class CircuitProfile:
    circuit_id: str
    canonical_name: str
    country: str
    location: str
    track_length_km: float
    scheduled_laps: int
    base_dry_lap_time_s: float
    pit_lane_speed_limit_kmh: int
    pit_lane_transit_loss_green_s: float
    pit_lane_transit_loss_sc_s: float
    tyre_stress_rating: int            # 1 (low) to 5 (extreme lateral stress)
    asphalt_abrasion_rating: int       # 1 (smooth) to 5 (highly abrasive)
    overtaking_difficulty_index: float # 0.0 (near-impossible, e.g. Monaco) to 1.0 (easy passing)
    typical_track_temp_c: float
    sc_probability_per_lap: float
    altitude_m: float
    drs_zones_count: int


CIRCUIT_PROFILES: Dict[str, CircuitProfile] = {
    "SPAIN": CircuitProfile(
        circuit_id="SPAIN",
        canonical_name="Circuit de Barcelona-Catalunya",
        country="Spain",
        location="Montmelo",
        track_length_km=4.657,
        scheduled_laps=66,
        base_dry_lap_time_s=78.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=21.5,
        pit_lane_transit_loss_sc_s=12.5,
        tyre_stress_rating=4,
        asphalt_abrasion_rating=4,
        overtaking_difficulty_index=0.45,
        typical_track_temp_c=38.0,
        sc_probability_per_lap=0.018,
        altitude_m=120.0,
        drs_zones_count=2
    ),
    "MONACO": CircuitProfile(
        circuit_id="MONACO",
        canonical_name="Circuit de Monaco",
        country="Monaco",
        location="Monte Carlo",
        track_length_km=3.337,
        scheduled_laps=78,
        base_dry_lap_time_s=74.5,
        pit_lane_speed_limit_kmh=60,
        pit_lane_transit_loss_green_s=19.5,
        pit_lane_transit_loss_sc_s=11.0,
        tyre_stress_rating=1,
        asphalt_abrasion_rating=1,
        overtaking_difficulty_index=0.05,  # Track position is absolute king!
        typical_track_temp_c=36.0,
        sc_probability_per_lap=0.045,
        altitude_m=15.0,
        drs_zones_count=1
    ),
    "SILVERSTONE": CircuitProfile(
        circuit_id="SILVERSTONE",
        canonical_name="Silverstone Circuit",
        country="Great Britain",
        location="Silverstone",
        track_length_km=5.891,
        scheduled_laps=52,
        base_dry_lap_time_s=88.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=25.0,
        pit_lane_transit_loss_sc_s=14.5,
        tyre_stress_rating=5,  # Maggotts/Becketts high-G lateral loading
        asphalt_abrasion_rating=4,
        overtaking_difficulty_index=0.72,
        typical_track_temp_c=30.0,
        sc_probability_per_lap=0.024,
        altitude_m=150.0,
        drs_zones_count=2
    ),
    "BAHRAIN": CircuitProfile(
        circuit_id="BAHRAIN",
        canonical_name="Bahrain International Circuit",
        country="Bahrain",
        location="Sakhir",
        track_length_km=5.412,
        scheduled_laps=57,
        base_dry_lap_time_s=92.0,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=22.5,
        pit_lane_transit_loss_sc_s=13.0,
        tyre_stress_rating=4,
        asphalt_abrasion_rating=5,  # Granitic high-roughness asphalt
        overtaking_difficulty_index=0.75,
        typical_track_temp_c=32.0,
        sc_probability_per_lap=0.020,
        altitude_m=10.0,
        drs_zones_count=3
    ),
    "MONZA": CircuitProfile(
        circuit_id="MONZA",
        canonical_name="Autodromo Nazionale Monza",
        country="Italy",
        location="Monza",
        track_length_km=5.793,
        scheduled_laps=53,
        base_dry_lap_time_s=81.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=24.0,
        pit_lane_transit_loss_sc_s=14.0,
        tyre_stress_rating=2,  # Low downforce, low lateral degradation
        asphalt_abrasion_rating=3,
        overtaking_difficulty_index=0.85,  # Slipstream + heavy braking zones
        typical_track_temp_c=36.0,
        sc_probability_per_lap=0.022,
        altitude_m=160.0,
        drs_zones_count=2
    ),
    "SPA": CircuitProfile(
        circuit_id="SPA",
        canonical_name="Circuit de Spa-Francorchamps",
        country="Belgium",
        location="Stavelot",
        track_length_km=7.004,
        scheduled_laps=44,
        base_dry_lap_time_s=105.0,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=23.5,
        pit_lane_transit_loss_sc_s=13.5,
        tyre_stress_rating=5,  # Eau Rouge / Raidillon compression + Pouhon
        asphalt_abrasion_rating=3,
        overtaking_difficulty_index=0.80,
        typical_track_temp_c=25.0,
        sc_probability_per_lap=0.030,
        altitude_m=420.0,
        drs_zones_count=2
    ),
    "HUNGARY": CircuitProfile(
        circuit_id="HUNGARY",
        canonical_name="Hungaroring",
        country="Hungary",
        location="Mogyorod",
        track_length_km=4.381,
        scheduled_laps=70,
        base_dry_lap_time_s=78.0,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=20.5,
        pit_lane_transit_loss_sc_s=12.0,
        tyre_stress_rating=3,
        asphalt_abrasion_rating=2,
        overtaking_difficulty_index=0.22,  # Monaco without walls
        typical_track_temp_c=45.0,
        sc_probability_per_lap=0.015,
        altitude_m=240.0,
        drs_zones_count=2
    ),
    "AUSTRIA": CircuitProfile(
        circuit_id="AUSTRIA",
        canonical_name="Red Bull Ring",
        country="Austria",
        location="Spielberg",
        track_length_km=4.318,
        scheduled_laps=71,
        base_dry_lap_time_s=67.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=20.0,
        pit_lane_transit_loss_sc_s=11.5,
        tyre_stress_rating=3,
        asphalt_abrasion_rating=3,
        overtaking_difficulty_index=0.78,
        typical_track_temp_c=34.0,
        sc_probability_per_lap=0.025,
        altitude_m=680.0,
        drs_zones_count=3
    ),
    "ZANDVOORT": CircuitProfile(
        circuit_id="ZANDVOORT",
        canonical_name="Circuit Zandvoort",
        country="Netherlands",
        location="Zandvoort",
        track_length_km=4.259,
        scheduled_laps=72,
        base_dry_lap_time_s=72.0,
        pit_lane_speed_limit_kmh=60,
        pit_lane_transit_loss_green_s=22.0,
        pit_lane_transit_loss_sc_s=12.5,
        tyre_stress_rating=4,  # Banked corners Turns 3 & 14
        asphalt_abrasion_rating=3,
        overtaking_difficulty_index=0.30,
        typical_track_temp_c=28.0,
        sc_probability_per_lap=0.028,
        altitude_m=5.0,
        drs_zones_count=2
    ),
    "SINGAPORE": CircuitProfile(
        circuit_id="SINGAPORE",
        canonical_name="Marina Bay Street Circuit",
        country="Singapore",
        location="Marina Bay",
        track_length_km=4.940,
        scheduled_laps=62,
        base_dry_lap_time_s=95.0,
        pit_lane_speed_limit_kmh=60,
        pit_lane_transit_loss_green_s=28.0,  # Long pit lane + 60 km/h
        pit_lane_transit_loss_sc_s=16.0,
        tyre_stress_rating=2,
        asphalt_abrasion_rating=2,
        overtaking_difficulty_index=0.35,
        typical_track_temp_c=34.0,
        sc_probability_per_lap=0.055,  # Historically 100% SC rate
        altitude_m=10.0,
        drs_zones_count=3
    ),
    "SUZUKA": CircuitProfile(
        circuit_id="SUZUKA",
        canonical_name="Suzuka International Racing Course",
        country="Japan",
        location="Suzuka",
        track_length_km=5.807,
        scheduled_laps=53,
        base_dry_lap_time_s=92.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=23.0,
        pit_lane_transit_loss_sc_s=13.5,
        tyre_stress_rating=5,  # Esses & 130R intense lateral loads
        asphalt_abrasion_rating=4,
        overtaking_difficulty_index=0.55,
        typical_track_temp_c=28.0,
        sc_probability_per_lap=0.022,
        altitude_m=50.0,
        drs_zones_count=1
    ),
    "COTA": CircuitProfile(
        circuit_id="COTA",
        canonical_name="Circuit of the Americas",
        country="United States",
        location="Austin",
        track_length_km=5.513,
        scheduled_laps=56,
        base_dry_lap_time_s=96.0,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=21.0,
        pit_lane_transit_loss_sc_s=12.0,
        tyre_stress_rating=4,
        asphalt_abrasion_rating=4,  # Bumpy surface + high lateral Turn 16-18
        overtaking_difficulty_index=0.70,
        typical_track_temp_c=38.0,
        sc_probability_per_lap=0.020,
        altitude_m=160.0,
        drs_zones_count=2
    ),
    "MEXICO": CircuitProfile(
        circuit_id="MEXICO",
        canonical_name="Autodromo Hermanos Rodriguez",
        country="Mexico",
        location="Mexico City",
        track_length_km=4.304,
        scheduled_laps=71,
        base_dry_lap_time_s=78.0,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=22.0,
        pit_lane_transit_loss_sc_s=12.5,
        tyre_stress_rating=2,  # Thin air reduces aerodynamic load & tyre wear
        asphalt_abrasion_rating=2,
        overtaking_difficulty_index=0.60,
        typical_track_temp_c=35.0,
        sc_probability_per_lap=0.024,
        altitude_m=2285.0,
        drs_zones_count=3
    ),
    "INTERLAGOS": CircuitProfile(
        circuit_id="INTERLAGOS",
        canonical_name="Autodromo Jose Carlos Pace",
        country="Brazil",
        location="Sao Paulo",
        track_length_km=4.309,
        scheduled_laps=71,
        base_dry_lap_time_s=72.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=21.0,
        pit_lane_transit_loss_sc_s=12.0,
        tyre_stress_rating=3,
        asphalt_abrasion_rating=3,
        overtaking_difficulty_index=0.80,
        typical_track_temp_c=36.0,
        sc_probability_per_lap=0.035,
        altitude_m=780.0,
        drs_zones_count=2
    ),
    "LAS_VEGAS": CircuitProfile(
        circuit_id="LAS_VEGAS",
        canonical_name="Las Vegas Strip Circuit",
        country="United States",
        location="Las Vegas",
        track_length_km=6.201,
        scheduled_laps=50,
        base_dry_lap_time_s=94.0,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=20.5,
        pit_lane_transit_loss_sc_s=11.5,
        tyre_stress_rating=2,
        asphalt_abrasion_rating=2,  # Low grip, smooth street surface, cool night temps
        overtaking_difficulty_index=0.85,  # 1.9km Strip straight
        typical_track_temp_c=16.0,
        sc_probability_per_lap=0.035,
        altitude_m=620.0,
        drs_zones_count=2
    ),
    "QATAR": CircuitProfile(
        circuit_id="QATAR",
        canonical_name="Lusail International Circuit",
        country="Qatar",
        location="Lusail",
        track_length_km=5.419,
        scheduled_laps=57,
        base_dry_lap_time_s=84.0,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=24.5,
        pit_lane_transit_loss_sc_s=14.0,
        tyre_stress_rating=5,  # Extreme sustained high-speed lateral g-forces
        asphalt_abrasion_rating=5,
        overtaking_difficulty_index=0.60,
        typical_track_temp_c=35.0,
        sc_probability_per_lap=0.022,
        altitude_m=15.0,
        drs_zones_count=1
    ),
    "ABU_DHABI": CircuitProfile(
        circuit_id="ABU_DHABI",
        canonical_name="Yas Marina Circuit",
        country="United Arab Emirates",
        location="Abu Dhabi",
        track_length_km=5.281,
        scheduled_laps=58,
        base_dry_lap_time_s=85.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=22.0,
        pit_lane_transit_loss_sc_s=12.5,
        tyre_stress_rating=3,
        asphalt_abrasion_rating=3,
        overtaking_difficulty_index=0.65,
        typical_track_temp_c=30.0,
        sc_probability_per_lap=0.018,
        altitude_m=10.0,
        drs_zones_count=2
    ),
    "AUSTRALIA": CircuitProfile(
        circuit_id="AUSTRALIA",
        canonical_name="Albert Park Circuit",
        country="Australia",
        location="Melbourne",
        track_length_km=5.278,
        scheduled_laps=58,
        base_dry_lap_time_s=79.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=20.0,
        pit_lane_transit_loss_sc_s=11.5,
        tyre_stress_rating=3,
        asphalt_abrasion_rating=2,
        overtaking_difficulty_index=0.65,
        typical_track_temp_c=32.0,
        sc_probability_per_lap=0.038,
        altitude_m=10.0,
        drs_zones_count=4
    ),
    "CHINA": CircuitProfile(
        circuit_id="CHINA",
        canonical_name="Shanghai International Circuit",
        country="China",
        location="Shanghai",
        track_length_km=5.451,
        scheduled_laps=56,
        base_dry_lap_time_s=96.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=22.5,
        pit_lane_transit_loss_sc_s=13.0,
        tyre_stress_rating=4,  # Turn 1-2 long snail corner causes front-left graining
        asphalt_abrasion_rating=3,
        overtaking_difficulty_index=0.75,
        typical_track_temp_c=28.0,
        sc_probability_per_lap=0.022,
        altitude_m=10.0,
        drs_zones_count=2
    ),
    "MIAMI": CircuitProfile(
        circuit_id="MIAMI",
        canonical_name="Miami International Autodrome",
        country="United States",
        location="Miami",
        track_length_km=5.412,
        scheduled_laps=57,
        base_dry_lap_time_s=90.0,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=21.0,
        pit_lane_transit_loss_sc_s=12.0,
        tyre_stress_rating=3,
        asphalt_abrasion_rating=3,
        overtaking_difficulty_index=0.65,
        typical_track_temp_c=42.0,  # High ambient & track surface heat
        sc_probability_per_lap=0.030,
        altitude_m=5.0,
        drs_zones_count=3
    ),
    "IMOLA": CircuitProfile(
        circuit_id="IMOLA",
        canonical_name="Autodromo Internazionale Enzo e Dino Ferrari",
        country="Italy",
        location="Imola",
        track_length_km=4.909,
        scheduled_laps=63,
        base_dry_lap_time_s=76.0,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=28.5,  # Very long pit lane entry & exit
        pit_lane_transit_loss_sc_s=16.5,
        tyre_stress_rating=3,
        asphalt_abrasion_rating=3,
        overtaking_difficulty_index=0.25,  # Narrow track, high track position value
        typical_track_temp_c=32.0,
        sc_probability_per_lap=0.026,
        altitude_m=40.0,
        drs_zones_count=1
    ),
    "CANADA": CircuitProfile(
        circuit_id="CANADA",
        canonical_name="Circuit Gilles-Villeneuve",
        country="Canada",
        location="Montreal",
        track_length_km=4.361,
        scheduled_laps=70,
        base_dry_lap_time_s=73.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=19.5,
        pit_lane_transit_loss_sc_s=11.0,
        tyre_stress_rating=2,  # Stop-and-go, heavy braking, low lateral stress
        asphalt_abrasion_rating=2,
        overtaking_difficulty_index=0.75,
        typical_track_temp_c=30.0,
        sc_probability_per_lap=0.040,
        altitude_m=15.0,
        drs_zones_count=2
    ),
    "BAKU": CircuitProfile(
        circuit_id="BAKU",
        canonical_name="Baku City Circuit",
        country="Azerbaijan",
        location="Baku",
        track_length_km=6.003,
        scheduled_laps=51,
        base_dry_lap_time_s=103.0,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=21.0,
        pit_lane_transit_loss_sc_s=12.0,
        tyre_stress_rating=2,
        asphalt_abrasion_rating=2,
        overtaking_difficulty_index=0.82,  # 2.2km flat out straight
        typical_track_temp_c=34.0,
        sc_probability_per_lap=0.048,
        altitude_m=-25.0,
        drs_zones_count=2
    ),
    "JEDDAH": CircuitProfile(
        circuit_id="JEDDAH",
        canonical_name="Jeddah Corniche Circuit",
        country="Saudi Arabia",
        location="Jeddah",
        track_length_km=6.174,
        scheduled_laps=50,
        base_dry_lap_time_s=89.5,
        pit_lane_speed_limit_kmh=80,
        pit_lane_transit_loss_green_s=20.5,
        pit_lane_transit_loss_sc_s=11.5,
        tyre_stress_rating=3,
        asphalt_abrasion_rating=2,
        overtaking_difficulty_index=0.70,
        typical_track_temp_c=30.0,
        sc_probability_per_lap=0.052,
        altitude_m=10.0,
        drs_zones_count=3
    ),
}

# Alias mapping from event names, grand prix titles, or locations to canonical keys
CIRCUIT_ALIASES: Dict[str, str] = {
    "SPANISH": "SPAIN",
    "BARCELONA": "SPAIN",
    "CATALUNYA": "SPAIN",
    "MONTE CARLO": "MONACO",
    "BRITISH": "SILVERSTONE",
    "GREAT BRITAIN": "SILVERSTONE",
    "SAKHIR": "BAHRAIN",
    "ITALIAN": "MONZA",
    "BELGIAN": "SPA",
    "HUNGARIAN": "HUNGARY",
    "HUNGARORING": "HUNGARY",
    "AUSTRIAN": "AUSTRIA",
    "RED BULL RING": "AUSTRIA",
    "DUTCH": "ZANDVOORT",
    "NETHERLANDS": "ZANDVOORT",
    "MARINA BAY": "SINGAPORE",
    "JAPANESE": "SUZUKA",
    "UNITED STATES": "COTA",
    "USA": "COTA",
    "AUSTIN": "COTA",
    "MEXICAN": "MEXICO",
    "MEXICO CITY": "MEXICO",
    "BRAZIL": "INTERLAGOS",
    "BRAZILIAN": "INTERLAGOS",
    "SAO PAULO": "INTERLAGOS",
    "VEGAS": "LAS_VEGAS",
    "LUSAIL": "QATAR",
    "YAS MARINA": "ABU_DHABI",
    "ABU DHABI": "ABU_DHABI",
    "AUSTRALIAN": "AUSTRALIA",
    "MELBOURNE": "AUSTRALIA",
    "ALBERT PARK": "AUSTRALIA",
    "CHINESE": "CHINA",
    "SHANGHAI": "CHINA",
    "EMILIA ROMAGNA": "IMOLA",
    "CANADIAN": "CANADA",
    "MONTREAL": "CANADA",
    "AZERBAIJAN": "BAKU",
    "SAUDI ARABIA": "JEDDAH",
    "SAUDI": "JEDDAH"
}


class CircuitDatabase:
    """Provides validated circuit engineering profiles."""

    @classmethod
    def resolve_circuit_key(cls, identifier: Optional[str]) -> str:
        """Normalizes any event or circuit string into a canonical circuit key."""
        if not identifier:
            return "SPAIN"
        clean = str(identifier).upper().replace("-", " ").replace("_", " ").strip()
        # Direct check
        if clean in CIRCUIT_PROFILES:
            return clean
        for alias, key in CIRCUIT_ALIASES.items():
            if alias in clean:
                return key
        for key in CIRCUIT_PROFILES.keys():
            if key in clean:
                return key
        return "SPAIN"

    @classmethod
    def get_circuit_profile(cls, identifier: Optional[str]) -> CircuitProfile:
        """Retrieves CircuitProfile for specified identifier, with robust fallback."""
        key = cls.resolve_circuit_key(identifier)
        return CIRCUIT_PROFILES.get(key, CIRCUIT_PROFILES["SPAIN"])

    @classmethod
    def get_all_circuits(cls) -> List[Dict[str, Any]]:
        """Returns metadata dictionary for all supported circuits."""
        return [asdict(p) for p in CIRCUIT_PROFILES.values()]
