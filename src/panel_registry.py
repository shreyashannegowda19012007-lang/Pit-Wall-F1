"""
Central Panel Registry & Workspace Layout Manager for F1 Pit-Wall Console.
Defines modular panel definitions, default pit-wall layout configurations, layout presets
(DEFAULT, DRIVER_ANALYSIS, STRATEGY, 3D_RACE_VIEW, TELEMETRY), and layout state persistence.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


class LayoutPreset:
    DEFAULT = "DEFAULT_PITWALL"
    DRIVER_ANALYSIS = "DRIVER_ANALYSIS"
    STRATEGY_SIMULATION = "STRATEGY_SIMULATION"
    THREE_D_RACE_VIEW = "3D_RACE_VIEW"
    TELEMETRY_ENGINEERING = "TELEMETRY_ENGINEERING"


@dataclass
class PanelDefinition:
    panel_id: str
    title: str
    icon: str
    description: str
    is_visible: bool = True
    is_collapsed: bool = False
    order: int = 1


class PanelRegistry:
    """
    Central Panel Registry for Pit-Wall Engineer Console.
    """

    @classmethod
    def get_all_panels(cls) -> Dict[str, PanelDefinition]:
        """Returns central dictionary of available console panels."""
        return {
            "top_bar": PanelDefinition("top_bar", "Top Session Bar", "⏱️", "Session status, clock, and connection metadata", order=1),
            "timing_tower": PanelDefinition("timing_tower", "Real-Time Timing Tower", "📊", "P1-P20 Live Leaderboard with gaps, intervals, and tyres", order=2),
            "track_view": PanelDefinition("track_view", "3D WebGL Track Viewer", "🏎️", "Interactive 3D circuit layout, 20-car positions, and POV cameras", order=3),
            "driver_telemetry": PanelDefinition("driver_telemetry", "Telemetry & Time-Loss Analysis", "📈", "Distance-aligned speed, throttle, brake, gear, and time loss", order=4),
            "strategy_panel": PanelDefinition("strategy_panel", "Monte Carlo & Decision Engine", "🎯", "Strategy recommendations, win/podium probabilities, and what-ifs", order=5),
            "bayesian_panel": PanelDefinition("bayesian_panel", "Bayesian Tyre State Updating", "🔬", "Posterior tyre degradation, prior vs posterior, variance shrinkage", order=6),
            "race_control": PanelDefinition("race_control", "Race Control Event Stream", "🚩", "Live/replay race messages (SC, VSC, Flags, Penalties)", order=7),
            "ai_engineer": PanelDefinition("ai_engineer", "AI Engineer QA Engine", "🤖", "Senior Performance Engineer AI with grounded evidence citations", order=8),
            "evaluation_dashboard": PanelDefinition("evaluation_dashboard", "System Evaluation & Benchmark", "🧪", "Reproducible system benchmarking, 95% bootstrap CIs, ablation", order=9)
        }

    @classmethod
    def get_layout_preset(cls, preset_name: str = LayoutPreset.DEFAULT) -> List[str]:
        """Returns visible panel IDs for selected layout preset."""
        if preset_name == LayoutPreset.DRIVER_ANALYSIS:
            return ["top_bar", "timing_tower", "driver_telemetry", "ai_engineer"]
        elif preset_name == LayoutPreset.STRATEGY_SIMULATION:
            return ["top_bar", "timing_tower", "strategy_panel", "bayesian_panel", "ai_engineer"]
        elif preset_name == LayoutPreset.THREE_D_RACE_VIEW:
            return ["top_bar", "track_view", "timing_tower", "race_control"]
        elif preset_name == LayoutPreset.TELEMETRY_ENGINEERING:
            return ["top_bar", "driver_telemetry", "timing_tower", "evaluation_dashboard"]
        else:
            # Default Pit-Wall Layout
            return ["top_bar", "timing_tower", "track_view", "driver_telemetry", "strategy_panel", "bayesian_panel", "race_control", "ai_engineer", "evaluation_dashboard"]
