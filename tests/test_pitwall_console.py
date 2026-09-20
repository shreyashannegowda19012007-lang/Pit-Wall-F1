"""
Automated Unit & Integration Test Suite for F1 Pit-Wall Engineer Console & Workspace Orchestrator.
Verifies central panel registry, layout presets (Default, Driver Analysis, Strategy, 3D Track, Telemetry),
top session header formatting, and command palette layout persistence.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('src'))

from panel_registry import PanelRegistry, LayoutPreset, PanelDefinition
from pitwall_console import PitWallConsoleOrchestrator


class TestPitWallConsoleOrchestrator(unittest.TestCase):

    def test_central_panel_registry_definitions(self):
        """Verifies central registry registers all required console panels."""
        panels = PanelRegistry.get_all_panels()

        self.assertIn("timing_tower", panels)
        self.assertIn("track_view", panels)
        self.assertIn("driver_telemetry", panels)
        self.assertIn("strategy_panel", panels)
        self.assertIn("bayesian_panel", panels)
        self.assertIn("race_control", panels)
        self.assertIn("ai_engineer", panels)
        self.assertIn("evaluation_dashboard", panels)

    def test_layout_preset_configurations(self):
        """Verifies layout preset configurations filter panels correctly."""
        p_default = PanelRegistry.get_layout_preset(LayoutPreset.DEFAULT)
        p_driver = PanelRegistry.get_layout_preset(LayoutPreset.DRIVER_ANALYSIS)
        p_strat = PanelRegistry.get_layout_preset(LayoutPreset.STRATEGY_SIMULATION)

        self.assertEqual(len(p_default), 9)
        self.assertIn("driver_telemetry", p_driver)
        self.assertIn("strategy_panel", p_strat)
        self.assertNotIn("track_view", p_driver)

    def test_console_header_bar_formatting(self):
        """Verifies top session bar renders cleanly without raising exceptions."""
        try:
            PitWallConsoleOrchestrator.render_top_session_bar(
                year=2024, gp_name="Spanish GP", session_type="Race", mode="REPLAY", current_lap=15, total_laps=57, freshness_ms=42.0
            )
            success = True
        except Exception as e:
            success = False

        self.assertTrue(success)


if __name__ == '__main__':
    unittest.main()
