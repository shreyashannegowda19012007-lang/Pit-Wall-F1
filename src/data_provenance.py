"""
Data Provenance, Source Discovery & Engineering Classification Subsystem.
Formally defines data classifications, provider specifications, channel metadata,
and explicit boundaries between publicly measurable, mathematically derived,
statistically estimated, hypothetical counterfactuals, and confidential team telemetry.
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class DataClassification(str, Enum):
    """
    Formal classification of data authenticity and engineering pedigree.
    """
    MEASURED = "MEASURED"          # Direct physical sensor or timing measurement (e.g., speed, lap time, weather)
    DERIVED = "DERIVED"            # Deterministic mathematical/physics calculation (e.g., acceleration ax, delta t)
    ESTIMATED = "ESTIMATED"        # Statistical, ML, or physical simulation model (e.g., tyre degradation rate, pit window)
    HYPOTHETICAL = "HYPOTHETICAL"  # Counterfactual what-if simulation (e.g., ideal lap, alternative strategy)
    UNAVAILABLE = "UNAVAILABLE"    # Proprietary/confidential telemetry not accessible from public sources


@dataclass
class ProviderInfo:
    """Detailed specifications and provenance of an upstream data provider."""
    provider_id: str
    display_name: str
    doc_url: str
    licensing: str
    update_frequency: str
    typical_latency_s: float
    supported_domains: List[str]
    rate_limit_policy: str
    authenticity_level: str
    description: str


@dataclass
class ChannelMetadata:
    """Formal definition of an engineering channel or metric."""
    channel_id: str
    display_name: str
    unit: str
    classification: DataClassification
    provider_id: str
    nominal_frequency_hz: float
    min_physical_bound: Optional[float]
    max_physical_bound: Optional[float]
    description: str


@dataclass
class ProvenanceRecord:
    """Provenance audit stamp attached to API responses and analytical outputs."""
    metric_name: str
    classification: DataClassification
    source_provider: str
    calculation_method: str
    units: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    confidence_score: float = 1.0
    assumptions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "classification": self.classification.value if isinstance(self.classification, DataClassification) else str(self.classification),
            "source_provider": self.source_provider,
            "calculation_method": self.calculation_method,
            "units": self.units,
            "timestamp": self.timestamp,
            "confidence_score": round(self.confidence_score, 3),
            "assumptions": self.assumptions,
            "limitations": self.limitations
        }


class DataProvenanceRegistry:
    """Central registry of data providers, engineering channels, and confidentiality boundaries."""

    PROVIDERS: Dict[str, ProviderInfo] = {
        "FASTF1": ProviderInfo(
            provider_id="FASTF1",
            display_name="FastF1 Official Timing & Telemetry Archive",
            doc_url="https://docs.fastf1.dev/",
            licensing="MIT License (Community Open Source)",
            update_frequency="Session completion (~15-30 min post-session)",
            typical_latency_s=0.05,
            supported_domains=["Laps", "Car Telemetry", "Position Coordinates", "Weather", "Race Control", "Circuit Info"],
            rate_limit_policy="Local SQLite/Parquet cached; respectful community CDN retrieval",
            authenticity_level="Authoritative Formula One Management (FOM) broadcast timing feed",
            description="Extracts raw broadcast telemetry, timing data, and track status from Formula One timing servers."
        ),
        "OPENF1": ProviderInfo(
            provider_id="OPENF1",
            display_name="OpenF1 Real-Time Telemetry API",
            doc_url="https://openf1.org/",
            licensing="Open Community / Fair Use",
            update_frequency="Near real-time (~3-5s during live Grand Prix sessions)",
            typical_latency_s=2.5,
            supported_domains=["Live Intervals", "Stints", "Pit Stops", "Radio Audio", "Real-Time Weather", "Race Control"],
            rate_limit_policy="3-4 req/sec cached with exponential backoff",
            authenticity_level="Direct official timing stream ingestion",
            description="Provides granular live session telemetry, pit stop durations, and team radio audio captures."
        ),
        "JOLPICA": ProviderInfo(
            provider_id="JOLPICA",
            display_name="Jolpica-F1 (Ergast API Successor)",
            doc_url="https://jolpi.ca/",
            licensing="CC-BY 4.0",
            update_frequency="Post-race official classification certification",
            typical_latency_s=0.2,
            supported_domains=["World Championship Standings", "Career History", "Constructors", "Circuit Coordinates"],
            rate_limit_policy="Cached 24h with in-memory TTL",
            authenticity_level="Official FIA Certified Results History",
            description="Authoritative database of Formula One World Championship standings and historical race results since 1950."
        ),
        "FIA_DOCUMENTS": ProviderInfo(
            provider_id="FIA_DOCUMENTS",
            display_name="FIA Official Decision & Regulatory Documents",
            doc_url="https://www.fia.com/documents/championships/fia-formula-one-world-championship-14",
            licensing="Official FIA Regulatory Public Record",
            update_frequency="Event-driven steward bulletins",
            typical_latency_s=60.0,
            supported_domains=["Sporting Regulations", "Technical Regulations", "Steward Infringements", "Power Unit Allocations"],
            rate_limit_policy="Curated regulatory knowledge base",
            authenticity_level="Legally binding FIA sporting authority",
            description="Official Formula One Sporting, Technical, and Financial Regulations published by the FIA."
        )
    }

    CHANNELS: Dict[str, ChannelMetadata] = {
        # MEASURED CHANNELS
        "Speed": ChannelMetadata("Speed", "Ground Speed", "km/h", DataClassification.MEASURED, "FASTF1", 10.0, 0.0, 385.0, "Wheel-derived vehicle ground velocity"),
        "Throttle": ChannelMetadata("Throttle", "Throttle Pedal Position", "%", DataClassification.MEASURED, "FASTF1", 10.0, 0.0, 100.0, "Driver throttle pedal application angle"),
        "Brake": ChannelMetadata("Brake", "Brake Pedal Application", "%", DataClassification.MEASURED, "FASTF1", 10.0, 0.0, 100.0, "Driver brake pedal application flag or pressure"),
        "RPM": ChannelMetadata("RPM", "Engine Crankshaft Speed", "RPM", DataClassification.MEASURED, "FASTF1", 10.0, 0.0, 15000.0, "Internal combustion engine crankshaft revolutions per minute"),
        "nGear": ChannelMetadata("nGear", "Transmission Gear Ratio", "gear", DataClassification.MEASURED, "FASTF1", 10.0, 0.0, 8.0, "Selected sequential gearbox gear (0 = Neutral, 1-8 forward)"),
        "DRS": ChannelMetadata("DRS", "Drag Reduction System Status", "code", DataClassification.MEASURED, "FASTF1", 10.0, 0.0, 14.0, "Hydraulic rear wing flap state indicator"),
        "LapTime": ChannelMetadata("LapTime", "Lap Duration", "s", DataClassification.MEASURED, "FASTF1", 1.0, 50.0, 180.0, "Timing transponder loop-to-loop duration"),
        "TrackTemp": ChannelMetadata("TrackTemp", "Track Surface Temperature", "°C", DataClassification.MEASURED, "FASTF1", 0.1, 0.0, 70.0, "Infrared optical pyrometer track temperature"),
        "AirTemp": ChannelMetadata("AirTemp", "Ambient Air Temperature", "°C", DataClassification.MEASURED, "FASTF1", 0.1, -10.0, 55.0, "Meteorological station ambient air temperature"),

        # DERIVED CHANNELS
        "LongitudinalAccel": ChannelMetadata("LongitudinalAccel", "Longitudinal Acceleration (ax)", "g", DataClassification.DERIVED, "FASTF1", 10.0, -6.5, 3.5, "Time-derivative of forward speed dv/dt divided by 9.81 m/s^2"),
        "LateralAccel": ChannelMetadata("LateralAccel", "Lateral Acceleration (ay)", "g", DataClassification.DERIVED, "FASTF1", 10.0, -6.5, 6.5, "Centripetal acceleration v^2/R derived from track curvature and speed"),
        "DeltaTime": ChannelMetadata("DeltaTime", "Delta Lap Time", "s", DataClassification.DERIVED, "FASTF1", 10.0, -20.0, 20.0, "Distance-interpolated differential elapsed time between two laps"),
        "Curvature": ChannelMetadata("Curvature", "Track Curvature (kappa)", "1/m", DataClassification.DERIVED, "FASTF1", 10.0, 0.0, 0.2, "Instantaneous curvature of vehicle trajectory"),

        # ESTIMATED CHANNELS
        "TyreDegradationSlope": ChannelMetadata("TyreDegradationSlope", "Wear Rate Slope (beta)", "s/lap", DataClassification.ESTIMATED, "FASTF1", 0.01, 0.005, 0.35, "Fuel-corrected linear OLS pace loss per lap"),
        "CompoundCrossover": ChannelMetadata("CompoundCrossover", "Crossover Lap", "lap", DataClassification.ESTIMATED, "FASTF1", 0.01, 1.0, 70.0, "Lap where older soft tyre pace matches fresh hard tyre pace"),
        "UndercutProbability": ChannelMetadata("UndercutProbability", "Undercut Success Probability", "%", DataClassification.ESTIMATED, "FASTF1", 0.01, 0.0, 100.0, "Stochastic delta window evaluation of pit stop gain"),

        # HYPOTHETICAL CHANNELS
        "IdealLapTime": ChannelMetadata("IdealLapTime", "Theoretical Best Lap Time", "s", DataClassification.HYPOTHETICAL, "FASTF1", 0.01, 50.0, 180.0, "Composite sum of personal best sector times across session"),
        "SimulatedFinishingPos": ChannelMetadata("SimulatedFinishingPos", "Monte Carlo Finishing Position", "position", DataClassification.HYPOTHETICAL, "FASTF1", 0.01, 1.0, 20.0, "Probabilistic finishing position from 100+ stochastic race runs"),

        # UNAVAILABLE CHANNELS
        "SuspensionTravel": ChannelMetadata("SuspensionTravel", "Suspension Potentiometer Displacement", "mm", DataClassification.UNAVAILABLE, "CONFIDENTIAL", 0.0, None, None, "Proprietary team damper and spring stroke telemetry"),
        "AerodynamicDownforce": ChannelMetadata("AerodynamicDownforce", "Aerodynamic Vertical Force (Fz)", "N", DataClassification.UNAVAILABLE, "CONFIDENTIAL", 0.0, None, None, "Proprietary wind tunnel and CFD ride-height aero maps"),
        "TyreBulkTemperature": ChannelMetadata("TyreBulkTemperature", "Internal Tyre Carcass Temperature", "°C", DataClassification.UNAVAILABLE, "CONFIDENTIAL", 0.0, None, None, "Confidential team internal tyre sensor telemetry"),
        "FuelFlowRate": ChannelMetadata("FuelFlowRate", "Instantaneous Fuel Mass Flow", "kg/h", DataClassification.UNAVAILABLE, "CONFIDENTIAL", 0.0, None, None, "FIA encrypted fuel flow meter telemetry (max 100 kg/h)"),
        "BatterySOC": ChannelMetadata("BatterySOC", "Hybrid Battery True State-of-Charge", "%", DataClassification.UNAVAILABLE, "CONFIDENTIAL", 0.0, None, None, "Confidential team energy management and cell voltage telemetry")
    }

    CONFIDENTIAL_BOUNDARIES = [
        "Suspension kinematics, spring rates, roll bar stiffness, and damper stroke telemetry.",
        "Aerodynamic downforce (Cl*A) and drag (Cd*A) look-up tables in engineering units.",
        "Internal tyre carcass temperature, tyre cavity air pressure, and contact patch thermal maps.",
        "Engine combustion chamber pressure, air-fuel ratio (lambda), and instant fuel mass flow.",
        "Hybrid battery cell State-of-Charge (SOC), MGU-K electrical torque curves, and power unit maps.",
        "Confidential car setup sheets: toe, camber, brake bias migration tables, and ballast distribution."
    ]

    @classmethod
    def get_provider(cls, provider_id: str) -> Optional[ProviderInfo]:
        return cls.PROVIDERS.get(provider_id.upper())

    @classmethod
    def get_channel(cls, channel_id: str) -> Optional[ChannelMetadata]:
        return cls.CHANNELS.get(channel_id)

    @classmethod
    def get_provenance_summary(cls) -> Dict[str, Any]:
        """Returns complete system data provenance overview."""
        return {
            "providers": {k: asdict(v) for k, v in cls.PROVIDERS.items()},
            "channels_count": len(cls.CHANNELS),
            "confidential_boundaries": cls.CONFIDENTIAL_BOUNDARIES,
            "classification_definitions": {
                DataClassification.MEASURED.value: "Direct sensor readings from official telemetry.",
                DataClassification.DERIVED.value: "Deterministic math/physics calculations from measurements.",
                DataClassification.ESTIMATED.value: "Statistical regressions, pace models, and tyre wear slopes.",
                DataClassification.HYPOTHETICAL.value: "Counterfactual ideal laps, alternative strategies, and Monte Carlo sims.",
                DataClassification.UNAVAILABLE.value: "Proprietary telemetry not accessible in public data."
            }
        }
