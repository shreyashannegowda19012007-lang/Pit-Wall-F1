"""
Database & Storage Architecture for F1 Time-Series Telemetry Pipeline.
Provides persistent relational storage (SQLite / PostgreSQL) for datasets, validation reports,
high-frequency telemetry samples, calculated features, and lineage metadata.
Includes composite indexes and bulk transaction processing for high-volume time-series queries.
"""

import sqlite3
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import logging

from src import config

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(config.CACHE_DIR, "f1_telemetry_pipeline.db")


class TelemetryStorageEngine:
    """
    Relational database interface managing persistence, indexing, and fast time-series retrieval.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_tables()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initializes relational database schema with composite indexes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Datasets Metadata Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                dataset_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_file TEXT,
                ingestion_timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL,
                driver_id TEXT NOT NULL,
                lap_number INTEGER,
                row_count INTEGER NOT NULL,
                schema_version TEXT NOT NULL,
                processing_version TEXT NOT NULL,
                checksum TEXT NOT NULL
            )
            """)

            # 2. Validation Reports Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_results (
                validation_id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                status TEXT NOT NULL,
                rows_checked INTEGER NOT NULL,
                rows_removed INTEGER NOT NULL,
                rows_repaired INTEGER NOT NULL,
                errors_json TEXT,
                warnings_json TEXT,
                channel_availability_json TEXT,
                validated_at TEXT NOT NULL,
                FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id)
            )
            """)

            # 3. Laps Metadata Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS laps (
                lap_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                driver_id TEXT NOT NULL,
                lap_number INTEGER NOT NULL,
                lap_time_s REAL,
                compound TEXT,
                tyre_life INTEGER,
                created_at TEXT NOT NULL
            )
            """)

            # 4. High-Volume Telemetry Samples Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_samples (
                sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id TEXT NOT NULL,
                lap_id TEXT NOT NULL,
                timestamp_s REAL NOT NULL,
                distance_m REAL NOT NULL,
                speed_kmh REAL NOT NULL,
                throttle_pct REAL,
                brake_pct REAL,
                gear INTEGER,
                rpm REAL,
                drs INTEGER,
                steering_deg REAL,
                FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id)
            )
            """)

            # 5. Lap Features Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS lap_features (
                feature_id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                driver_id TEXT NOT NULL,
                lap_number INTEGER,
                features_json TEXT NOT NULL,
                calculated_at TEXT NOT NULL,
                FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id)
            )
            """)

            # 6. Lineage Tracking Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_lineage (
                lineage_id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                raw_dataset_id TEXT NOT NULL,
                cleaned_dataset_id TEXT NOT NULL,
                aligned_dataset_id TEXT NOT NULL,
                feature_set_id TEXT NOT NULL,
                processing_version TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)

            # Composite Indexes for Query Performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_samples_lap_dist ON telemetry_samples(lap_id, distance_m)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_samples_dataset ON telemetry_samples(dataset_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_laps_driver_session ON laps(session_id, driver_id, lap_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_session ON datasets(session_id, driver_id)")

            conn.commit()

    def save_dataset_metadata(self, meta: Dict[str, Any]):
        """Persists dataset metadata record."""
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO datasets
            (dataset_id, source, source_file, ingestion_timestamp, session_id, driver_id, lap_number, row_count, schema_version, processing_version, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meta["dataset_id"], meta["source"], meta.get("source_file"),
                meta["ingestion_timestamp"], meta["session_id"], meta["driver_id"],
                meta.get("lap_number"), meta["row_count"], meta["schema_version"],
                meta["processing_version"], meta["checksum"]
            ))
            conn.commit()

    def save_validation_result(self, val_dict: Dict[str, Any], dataset_id: str):
        """Persists structured validation diagnostic report."""
        val_id = f"VAL-{dataset_id[:16]}"
        now = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO validation_results
            (validation_id, dataset_id, status, rows_checked, rows_removed, rows_repaired, errors_json, warnings_json, channel_availability_json, validated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                val_id, dataset_id, val_dict["validation_status"],
                val_dict.get("rows_checked", 0), val_dict.get("rows_removed", 0), val_dict.get("rows_repaired", 0),
                json.dumps(val_dict.get("errors", [])), json.dumps(val_dict.get("warnings", [])),
                json.dumps(val_dict.get("channel_availability", {})), now
            ))
            conn.commit()

    def save_telemetry_samples(self, df: pd.DataFrame, dataset_id: str, lap_id: str):
        """Bulk inserts high-volume telemetry samples using parameterized transactions."""
        if df is None or df.empty:
            return

        records = []
        for _, row in df.iterrows():
            t_s = float(row.get('timestamp_s', 0.0))
            if t_s == 0.0 and 'Time' in row and hasattr(row['Time'], 'total_seconds'):
                t_s = row['Time'].total_seconds()

            records.append((
                dataset_id,
                lap_id,
                t_s,
                float(row.get('Distance', row.get('distance_m', 0.0))),
                float(row.get('Speed', row.get('speed_kmh', 0.0))),
                float(row.get('Throttle', row.get('throttle_pct', 0.0))) if pd.notna(row.get('Throttle', row.get('throttle_pct'))) else None,
                float(row.get('Brake', row.get('brake_pct', 0.0))) if pd.notna(row.get('Brake', row.get('brake_pct'))) else None,
                int(row.get('nGear', row.get('gear', 0))) if pd.notna(row.get('nGear', row.get('gear'))) else None,
                float(row.get('RPM', np.nan)) if pd.notna(row.get('RPM')) else None,
                int(row.get('DRS', np.nan)) if pd.notna(row.get('DRS')) else None,
                float(row.get('Steering', np.nan)) if pd.notna(row.get('Steering')) else None
            ))

        with self.get_connection() as conn:
            conn.execute("DELETE FROM telemetry_samples WHERE dataset_id = ?", (dataset_id,))
            conn.executemany("""
            INSERT INTO telemetry_samples
            (dataset_id, lap_id, timestamp_s, distance_m, speed_kmh, throttle_pct, brake_pct, gear, rpm, drs, steering_deg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            conn.commit()

    def save_features(self, feat_dict: Dict[str, Any]):
        """Persists feature dataset record."""
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO lap_features
            (feature_id, dataset_id, session_id, driver_id, lap_number, features_json, calculated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                feat_dict["feature_set_id"], feat_dict["dataset_id"], feat_dict["session_id"],
                feat_dict["driver_id"], feat_dict.get("lap_number"), json.dumps(feat_dict),
                feat_dict["calculated_at"]
            ))
            conn.commit()

    def save_lineage(self, lineage_dict: Dict[str, Any]):
        """Persists lineage record connecting raw dataset to final analysis."""
        with self.get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO data_lineage
            (lineage_id, analysis_id, raw_dataset_id, cleaned_dataset_id, aligned_dataset_id, feature_set_id, processing_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lineage_dict["lineage_id"], lineage_dict["analysis_id"],
                lineage_dict["raw_dataset_id"], lineage_dict["cleaned_dataset_id"],
                lineage_dict["aligned_dataset_id"], lineage_dict["feature_set_id"],
                lineage_dict["processing_version"], lineage_dict["created_at"]
            ))
            conn.commit()

    def get_dataset_by_id(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves dataset metadata by dataset_id."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM datasets WHERE dataset_id = ?", (dataset_id,)).fetchone()
            return dict(row) if row else None

    def get_telemetry_samples(self, dataset_id: str) -> pd.DataFrame:
        """Retrieves high-volume telemetry samples for a given dataset."""
        with self.get_connection() as conn:
            query = "SELECT * FROM telemetry_samples WHERE dataset_id = ? ORDER BY distance_m ASC"
            return pd.read_sql_query(query, conn, params=(dataset_id,))

    def get_corner_telemetry(self, dataset_id: str, entry_m: float, exit_m: float) -> pd.DataFrame:
        """Indexed range query fetching telemetry samples within a corner window."""
        with self.get_connection() as conn:
            query = """
            SELECT * FROM telemetry_samples
            WHERE dataset_id = ? AND distance_m >= ? AND distance_m <= ?
            ORDER BY distance_m ASC
            """
            return pd.read_sql_query(query, conn, params=(dataset_id, entry_m, exit_m))

    def get_lineage(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves complete lineage trace for an analytical result."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM data_lineage WHERE analysis_id = ? OR raw_dataset_id = ?", (analysis_id, analysis_id)).fetchone()
            return dict(row) if row else None
