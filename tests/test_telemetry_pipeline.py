"""
Comprehensive Automated Test Suite & Performance Benchmark for F1 Time-Series Telemetry Data Pipeline.
Verifies all 10 pipeline stages: Ingestion -> Validation -> Cleaning -> Sync -> Alignment -> Features -> Storage -> Lineage -> API -> Performance.
"""

import unittest
import numpy as np
import pandas as pd
import time
import os
import sys

sys.path.insert(0, os.path.abspath('src'))

from telemetry_schema import validate_schema_compliance, TELEMETRY_SCHEMA
from telemetry_ingestion import TelemetryIngestionService, IngestedDataset
from telemetry_validation import validate_telemetry_df, TelemetryValidationResult
from telemetry_cleaning import clean_telemetry_df
from telemetry_sync import synchronize_telemetry_channels
from lap_alignment import align_laps_by_distance
from telemetry_features import FeatureEngineeringService, FeatureDataset
from telemetry_storage import TelemetryStorageEngine
from telemetry_pipeline import TelemetryPipeline, PipelineRunResult
from telemetry_api import TelemetryAPIService


class TestTelemetryDataPipeline(unittest.TestCase):

    def setUp(self):
        # Generate synthetic high-frequency telemetry dataset (2000 samples)
        self.num_samples = 2000
        time_sec = np.linspace(0.0, 90.0, self.num_samples)
        dist_grid = np.linspace(0.0, 5000.0, self.num_samples)
        # Create clear corner speed drops (dropping from 300 to 100 km/h)
        speed = 300.0 - 200.0 * np.exp(-((dist_grid - 2500.0) / 150.0)**2)
        throttle = np.where(speed > 220, 100.0, 0.0)
        brake = np.where(speed <= 220, 80.0, 0.0)
        gear = np.where(speed < 150, 3, np.where(speed < 250, 6, 8))
        rpm = speed * 45.0

        self.df_raw = pd.DataFrame({
            'timestamp_s': time_sec,
            'Distance': dist_grid,
            'Speed': speed,
            'Throttle': throttle,
            'Brake': brake,
            'nGear': gear,
            'RPM': rpm,
            'DRS': np.zeros(self.num_samples, dtype=int)
        })

    def test_stage1_ingestion(self):
        dataset = TelemetryIngestionService.ingest_from_dataframe(
            df=self.df_raw,
            source="SYNTHETIC_TEST",
            session_id="2024_SPAIN_RACE",
            driver_id="VER",
            lap_number=14
        )
        self.assertTrue(dataset.dataset_id.startswith("DS-VER-2024_SPAIN_RACE"))
        self.assertEqual(dataset.row_count, self.num_samples)
        self.assertIsNotNone(dataset.checksum)
        self.assertEqual(len(dataset.checksum), 64)  # SHA-256 length

    def test_stage2_schema_and_validation(self):
        is_compliant, errors, warnings = validate_schema_compliance(self.df_raw)
        self.assertTrue(is_compliant)
        self.assertEqual(len(errors), 0)

        val_result = validate_telemetry_df(self.df_raw)
        self.assertTrue(val_result.is_valid)
        self.assertEqual(val_result.validation_status, "PASSED")
        self.assertTrue(val_result.channel_availability['speed'])

    def test_stage3_cleaning(self):
        # Create dirty copy with un-sorted duplicate distance
        dirty_df = self.df_raw.copy()
        dirty_df.loc[10, 'Distance'] = dirty_df.loc[9, 'Distance']  # Duplicate distance

        cleaned_df, meta = clean_telemetry_df(dirty_df)
        self.assertFalse(cleaned_df.empty)
        self.assertTrue(meta['rows_removed'] >= 1)
        self.assertTrue(np.all(np.diff(cleaned_df['Distance'].values) >= 0.0))

    def test_stage4_multi_frequency_sync(self):
        synced_df, sync_meta = synchronize_telemetry_channels(self.df_raw, target_freq_hz=100.0)
        self.assertFalse(synced_df.empty)
        self.assertEqual(sync_meta['target_freq_hz'], 100.0)
        self.assertEqual(sync_meta['interpolation_methods']['Speed'], '1d_linear_interpolation')
        self.assertEqual(sync_meta['interpolation_methods']['nGear'], 'nearest_neighbor_step')

    def test_stage5_distance_alignment(self):
        aligned_df, align_meta = align_laps_by_distance(
            self.df_raw, self.df_raw,
            grid_step_m=1.0,
            driver_a_code="VER",
            driver_b_code="HAM"
        )
        self.assertFalse(aligned_df.empty)
        self.assertIn('DeltaTime', aligned_df.columns)
        self.assertAlmostEqual(align_meta['integrated_time_delta_s'], 0.0, delta=0.01)

    def test_stage6_feature_engineering(self):
        feat_ds = FeatureEngineeringService.extract_lap_features(
            self.df_raw, dataset_id="DS-TEST-001", session_id="SPAIN_2024", driver_id="VER", lap_number=14
        )
        self.assertIsNotNone(feat_ds.lap_features)
        self.assertTrue(feat_ds.lap_features.max_speed_kmh > 250.0)
        self.assertTrue(len(feat_ds.corner_features) > 0)

    def test_stage7_database_storage(self):
        test_db_path = "f1_cache/test_pipeline_storage.db"
        storage = TelemetryStorageEngine(db_path=test_db_path)

        ingested = TelemetryIngestionService.ingest_from_dataframe(self.df_raw, source="TEST", session_id="TEST_SESS", driver_id="VER")
        storage.save_dataset_metadata(ingested.get_metadata())
        storage.save_telemetry_samples(self.df_raw, ingested.dataset_id, "LAP-VER-1")

        fetched_meta = storage.get_dataset_by_id(ingested.dataset_id)
        self.assertIsNotNone(fetched_meta)
        self.assertEqual(fetched_meta['driver_id'], "VER")

        fetched_samples = storage.get_telemetry_samples(ingested.dataset_id)
        self.assertEqual(len(fetched_samples), len(self.df_raw))

    def test_stage8_end_to_end_pipeline(self):
        test_db_path = "f1_cache/test_pipeline_e2e.db"
        pipeline = TelemetryPipeline(storage_engine=TelemetryStorageEngine(db_path=test_db_path))

        res = pipeline.process_session_telemetry(
            raw_data=self.df_raw,
            session_id="SPAIN_2024",
            driver_id="VER",
            lap_number=14,
            source="SYNTHETIC_UNITTEST"
        )

        self.assertTrue(res.success)
        self.assertTrue(res.raw_dataset_id.startswith("DS-VER-SPAIN_2024"))
        self.assertTrue(res.cleaned_dataset_id.startswith("CLEAN-VER-SPAIN_2024"))
        self.assertTrue(res.aligned_dataset_id.startswith("ALIGN-VER-SPAIN_2024"))
        self.assertTrue(res.feature_set_id.startswith("FEAT-VER-SPAIN_2024"))
        self.assertIsNotNone(res.lineage)

    def test_stage9_api_service_integration(self):
        api = TelemetryAPIService()
        ingest_res = api.ingest_telemetry_payload(
            data_payload=self.df_raw,
            session_id="2024_SPAIN",
            driver_id="VER",
            lap_number=1,
            source="API_TEST"
        )
        self.assertTrue(ingest_res['success'])

    def test_stage10_performance_benchmark(self):
        """Measures execution throughput for a 100,000-sample telemetry workload."""
        benchmark_samples = 100000
        dist_bm = np.linspace(0.0, 5000.0, benchmark_samples)
        speed_bm = 220.0 + 80.0 * np.sin(2.0 * np.pi * dist_bm / 1000.0)

        df_large = pd.DataFrame({
            'timestamp_s': np.linspace(0.0, 90.0, benchmark_samples),
            'Distance': dist_bm,
            'Speed': speed_bm,
            'Throttle': np.where(speed_bm > 220, 100.0, 0.0),
            'Brake': np.where(speed_bm <= 220, 80.0, 0.0),
            'nGear': np.where(speed_bm < 150, 3, 7)
        })

        t0 = time.perf_counter()
        ingested = TelemetryIngestionService.ingest_from_dataframe(df_large, source="BENCHMARK", session_id="BM_SESS", driver_id="VER")
        t_ingest = time.perf_counter() - t0

        t0 = time.perf_counter()
        val_res = validate_telemetry_df(df_large)
        t_validate = time.perf_counter() - t0

        t0 = time.perf_counter()
        cleaned_df, _ = clean_telemetry_df(df_large)
        t_clean = time.perf_counter() - t0

        t0 = time.perf_counter()
        synced_df, _ = synchronize_telemetry_channels(cleaned_df, target_freq_hz=100.0)
        t_sync = time.perf_counter() - t0

        t0 = time.perf_counter()
        feats = FeatureEngineeringService.extract_lap_features(synced_df, dataset_id=ingested.dataset_id, session_id="BM_SESS", driver_id="VER")
        t_features = time.perf_counter() - t0

        print(f"\n=== PIPELINE PERFORMANCE BENCHMARK ({benchmark_samples:,} SAMPLES) ===")
        print(f"- Ingestion Time:       {t_ingest*1000.0:.2f} ms")
        print(f"- Validation Time:      {t_validate*1000.0:.2f} ms")
        print(f"- Cleaning Time:        {t_clean*1000.0:.2f} ms")
        print(f"- Synchronization Time: {t_sync*1000.0:.2f} ms")
        print(f"- Feature Extraction:   {t_features*1000.0:.2f} ms")
        print(f"- Total Pipeline Latency: {(t_ingest + t_validate + t_clean + t_sync + t_features)*1000.0:.2f} ms")

        self.assertTrue(t_validate < 2.0)  # Validation must take under 2 seconds for 100k samples


if __name__ == '__main__':
    unittest.main()
