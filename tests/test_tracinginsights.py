import unittest
import pandas as pd
import numpy as np
import sys
import os
import base64

# Add src to python path
sys.path.insert(0, os.path.abspath('src'))

import tracinginsights
import race_simulator

class TestTracingInsights(unittest.TestCase):

    def setUp(self):
        # Create a mock laps dataframe with stints
        self.mock_laps = pd.DataFrame({
            'Driver': ['VER', 'VER', 'VER', 'HAM', 'HAM', 'HAM'],
            'DriverNumber': ['1', '1', '1', '44', '44', '44'],
            'LapNumber': [1, 2, 3, 1, 2, 3],
            'LapTime': pd.to_timedelta([90.0, 89.5, 89.0, 91.0, 90.2, 89.8], unit='s'),
            'Compound': ['SOFT', 'SOFT', 'SOFT', 'MEDIUM', 'MEDIUM', 'MEDIUM'],
            'Stint': [1, 1, 1, 1, 1, 1],
            'PitInTime': [pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT],
            'PitOutTime': [pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT],
            'Time': pd.to_timedelta([90.0, 179.5, 268.5, 91.0, 181.2, 271.0], unit='s'),
            'Date': pd.to_datetime([
                "2024-06-23T13:31:30Z", "2024-06-23T13:32:59Z", "2024-06-23T13:34:28Z",
                "2024-06-23T13:31:31Z", "2024-06-23T13:33:01Z", "2024-06-23T13:34:30Z"
            ])
        })

        # Create a mock results dataframe
        self.mock_results = pd.DataFrame({
            'Abbreviation': ['VER', 'HAM'],
            'TeamColor': ['3671C6', '27F4D2'],
            'TeamName': ['Red Bull Racing', 'Mercedes'],
            'DriverNumber': ['1', '44']
        })

    def test_driver_color_resolving(self):
        color_ver = tracinginsights.get_driver_color('VER', self.mock_results)
        self.assertEqual(color_ver, '#3671C6')

        color_alo = tracinginsights.get_driver_color('ALO')
        self.assertEqual(color_alo, '#229971')

        color_unknown = tracinginsights.get_driver_color('XYZ')
        self.assertEqual(color_unknown, '#4A90E2')

    def test_fuel_corrected_pace_calculation(self):
        corrected_df = tracinginsights.calculate_fuel_corrected_pace(self.mock_laps, fuel_burn_delta=0.03)
        self.assertIn('FuelCorrected_s', corrected_df.columns)

        # VER Lap 1: L_total = 3, L_current = 1, Raw = 90s
        # t_corrected = 90 - (3 - 1) * 0.03 = 89.94s
        ver_l1 = corrected_df[(corrected_df['Driver'] == 'VER') & (corrected_df['LapNumber'] == 1)].iloc[0]
        self.assertAlmostEqual(ver_l1['FuelCorrected_s'], 89.94)

    def test_tyre_smoothing_ema(self):
        smoothed_df = tracinginsights.apply_tyre_smoothing(self.mock_laps, alpha=0.3, fuel_burn_delta=0.03)
        self.assertIn('FuelCorrected_s', smoothed_df.columns)

        # VER Lap 1: initial value = 89.94s
        # VER Lap 2 raw corrected = 89.47s
        # VER Lap 2 EMA = 0.3 * 89.47 + 0.7 * 89.94 = 89.799s
        ver_l2 = smoothed_df[(smoothed_df['Driver'] == 'VER') & (smoothed_df['LapNumber'] == 2)].iloc[0]
        self.assertAlmostEqual(ver_l2['FuelCorrected_s'], 89.799)

    def test_corner_apex_detection(self):
        distance = np.linspace(0, 1000, 101)
        speed = 250.0 - 100.0 * np.sin(2.0 * np.pi * distance / 1000.0) # speed drops to minimum at 250m
        corners = tracinginsights.detect_corners_from_speed(distance, speed)
        self.assertTrue(len(corners) > 0)
        self.assertAlmostEqual(corners[0]['distance'], 250.0, delta=20.0)

    def test_radio_lap_mapping(self):
        mock_radio = [
            {"driver_number": 1, "transcript": "Box Box Max", "date": "2024-06-23T13:32:00Z"},
            {"driver_number": 44, "transcript": "Tires are good Lewis", "date": "2024-06-23T13:34:00Z"}
        ]
        mapped = tracinginsights.map_radio_to_laps(self.mock_laps, mock_radio)
        self.assertEqual(len(mapped), 2)

        ver_msg = next(m for m in mapped if m['driver'] == 'VER')
        self.assertEqual(ver_msg['lap'], 2)

    def test_fia_documents_fetching(self):
        docs = tracinginsights.fetch_fia_documents(2024, "Spain")
        self.assertEqual(len(docs), 0)



    def test_active_inference_strategy_suggestor(self):
        # Build mock rankings
        r1 = race_simulator.SimulationResult(
            strategy_name="Stay Out", expected_finish_time=3200.0,
            expected_position=2, expected_gap=0.0, win_probability=0.0,
            podium_probability=1.0, avg_lap_time=80.0, total_deg_cost=0.0,
            position_delta=0, risk_score=0.2, strategy_score=80.0,
            reasoning="Pace target baseline."
        )
        # Undercut yields 5.0 seconds savings
        r2 = race_simulator.SimulationResult(
            strategy_name="Pit Now (Soft)", expected_finish_time=3195.0,
            expected_position=1, expected_gap=-5.0, win_probability=0.8,
            podium_probability=1.0, avg_lap_time=79.8, total_deg_cost=0.0,
            position_delta=1, risk_score=0.1, strategy_score=95.0,
            reasoning="Fastest option."
        )

        suggestor = race_simulator.active_inference_strategy_suggestor([r2, r1], baseline_strategy_name="Stay Out")
        self.assertTrue(suggestor["action_flag"])
        self.assertEqual(suggestor["priority"], "CRITICAL")
        self.assertEqual(suggestor["best_strategy"], "Pit Now (Soft)")
        self.assertEqual(suggestor["expected_p50_gain"], 5.0)

if __name__ == '__main__':
    unittest.main()
